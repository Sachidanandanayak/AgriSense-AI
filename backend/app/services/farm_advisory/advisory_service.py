"""Evidence-Based Farm Advisory Service implementation.

Converts Phase 8 crop recommendations and multi-source environmental context into
transparent, source-backed agricultural advisory information grounded in FAO ECOCROP
and FAO-56 methodologies.
"""

from __future__ import annotations

import logging
from typing import Sequence

from app.schemas.satellite import SatelliteResponse
from app.schemas.soil import SoilResponse
from app.schemas.weather import WeatherResponse
from app.services.farm_advisory.compatibility import (
    evaluate_crop_environmental_compatibility,
)
from app.services.farm_advisory.exceptions import (
    CropRequirementNotFoundError,
    InvalidAdvisoryRequestError,
)
from app.services.farm_advisory.explanation import (
    generate_advisory_explanations,
    generate_advisory_limitations,
)
from app.services.farm_advisory.requirements import (
    CropRequirementRepository,
    crop_requirement_repository,
)
from app.services.farm_advisory.schemas import (
    ADVISORY_DISCLAIMER,
    CompatibilityStatus,
    CropAdvisoryItem,
    DataQualityAudit,
    FarmAdvisoryRequest,
    FarmAdvisoryResponse,
    SatelliteEnvironmentalContext,
    WaterAdvisory,
)
from app.services.farm_advisory.validators import (
    audit_data_freshness,
    validate_advisory_coordinates,
    validate_advisory_date,
)
from app.services.farm_advisory.water_advisory import evaluate_water_advisory
from app.services.recommendation.recommendation_service import (
    RecommendationService,
    recommendation_service,
)
from app.services.recommendation.schemas import (
    EnvironmentalContext,
    RecommendationRequest,
    RecommendationResponse,
)

logger = logging.getLogger(__name__)


class FarmAdvisoryService:
    """Service orchestrating evidence-based farm advisory reporting."""

    def __init__(
        self,
        rec_service: RecommendationService | None = None,
        req_repository: CropRequirementRepository | None = None,
    ) -> None:
        """Initialize advisory service with dependencies."""
        self.recommendation_service = rec_service or recommendation_service
        self.requirement_repository = req_repository or crop_requirement_repository

    async def generate_advisory(self, request: FarmAdvisoryRequest) -> FarmAdvisoryResponse:
        """Generate evidence-based farm advisory report for a farm location."""
        # 1. Validate spatial and temporal parameters
        lat, lon = validate_advisory_coordinates(request.latitude, request.longitude)
        obs_date = validate_advisory_date(request.observation_date)

        # 2. Resolve or execute Phase 8 Recommendation
        rec_response: RecommendationResponse
        if request.recommendation_response is not None:
            # Direct reuse of existing Phase 8 response (no duplicate inference)
            rec_response = request.recommendation_response
        else:
            rec_request = RecommendationRequest(
                latitude=lat,
                longitude=lon,
                observation_date=obs_date,
                agricultural_inputs=request.agricultural_inputs,
                top_k=request.top_k,
                weather_context=request.weather_context,
                satellite_context=request.satellite_context,
                soil_context=request.soil_context,
                fetch_live_weather=request.fetch_live_weather,
                fetch_live_satellite=request.fetch_live_satellite,
                fetch_live_soil=request.fetch_live_soil,
            )
            rec_response = await self.recommendation_service.generate_recommendation(rec_request)

        # 3. Extract environmental context and recommendation items
        weather: WeatherResponse | None = rec_response.environmental_context.weather
        satellite: SatelliteResponse | None = rec_response.environmental_context.satellite
        soil: SoilResponse | None = rec_response.environmental_context.soil

        # 4. Audit data freshness and initialize risk flags
        stale_sources, staleness_warnings = audit_data_freshness(weather, satellite, obs_date)
        all_risk_flags: set[str] = set()

        if stale_sources:
            all_risk_flags.add("stale_environmental_data")
        if weather is None:
            all_risk_flags.add("weather_data_missing")
        if satellite is None:
            all_risk_flags.add("satellite_data_missing")
        if soil is None:
            all_risk_flags.add("soil_data_missing")

        # 5. Extract observed environmental values for compatibility evaluation
        # Temperature: preference for live weather, then agricultural input
        observed_temp: float | None = None
        if weather is not None and weather.temperature_c is not None:
            observed_temp = weather.temperature_c
        elif request.agricultural_inputs is not None:
            observed_temp = request.agricultural_inputs.temperature
        elif request.temperature is not None:
            observed_temp = request.temperature

        # Rainfall: preference for seasonal agricultural input, then live weather
        observed_rain: float | None = None
        if request.agricultural_inputs is not None:
            observed_rain = request.agricultural_inputs.rainfall
        elif request.rainfall is not None:
            observed_rain = request.rainfall
        elif weather is not None and weather.rainfall_mm is not None:
            observed_rain = weather.rainfall_mm

        # Soil pH: preference for digital soil mapping (SoilGrids), then agricultural input
        observed_ph: float | None = None
        if soil is not None and soil.soil is not None and soil.soil.ph is not None:
            observed_ph = soil.soil.ph
        elif request.agricultural_inputs is not None:
            observed_ph = request.agricultural_inputs.ph
        elif request.ph is not None:
            observed_ph = request.ph

        # Soil Texture percentages from SoilGrids
        clay_pct: float | None = None
        sand_pct: float | None = None
        silt_pct: float | None = None
        if soil is not None and soil.soil is not None:
            clay_pct = soil.soil.clay_pct
            sand_pct = soil.soil.sand_pct
            silt_pct = soil.soil.silt_pct

        # 6. Evaluate compatibility for each recommended crop candidate
        crop_advisories: list[CropAdvisoryItem] = []

        for rec_item in rec_response.recommendations:
            crop_key = rec_item.crop.strip().lower()
            requirement = self.requirement_repository.get_requirement(crop_key)

            compat_status, var_evals, crop_risks = evaluate_crop_environmental_compatibility(
                requirement=requirement,
                temperature_c=observed_temp,
                rainfall_mm=observed_rain,
                soil_ph=observed_ph,
                clay_pct=clay_pct,
                sand_pct=sand_pct,
                silt_pct=silt_pct,
            )

            # Accumulate risk flags
            all_risk_flags.update(crop_risks)

            # Growth cycle information
            cycle_info: str | None = None
            if (
                requirement is not None
                and requirement.crop_cycle_min_days is not None
                and requirement.crop_cycle_max_days is not None
            ):
                cycle_info = (
                    f"{requirement.crop_cycle_min_days} to "
                    f"{requirement.crop_cycle_max_days} days (FAO ECOCROP)"
                )

            # Build agronomic advisory notes
            notes: list[str] = []
            if requirement is None:
                notes.append(
                    f"Authoritative FAO ECOCROP requirement data is currently unavailable for '{crop_key}'."
                )
            else:
                for v_name, eval_item in var_evals.items():
                    if eval_item.status == CompatibilityStatus.UNFAVORABLE:
                        notes.append(
                            f"Agronomic Warning ({eval_item.variable}): {eval_item.reason}"
                        )
                    elif eval_item.status == CompatibilityStatus.CAUTION:
                        notes.append(
                            f"Management Note ({eval_item.variable}): {eval_item.reason}"
                        )

            crop_advisory = CropAdvisoryItem(
                crop=rec_item.crop,
                scientific_name=requirement.scientific_name if requirement else None,
                rank=rec_item.rank,
                probability_estimate=rec_item.probability_estimate,
                confidence_percentage=rec_item.confidence_percentage,
                overall_compatibility=compat_status,
                compatibility_evaluations=var_evals,
                growth_cycle_days=cycle_info,
                risk_flags=crop_risks,
                advisory_notes=notes,
                requirement_provenance=requirement.provenance if requirement else None,
            )
            crop_advisories.append(crop_advisory)

        # 7. Evaluate Water-Related Advisory
        top_crop_req = (
            self.requirement_repository.get_requirement(rec_response.recommendations[0].crop)
            if rec_response.recommendations
            else None
        )
        water_advisory = evaluate_water_advisory(
            weather=weather,
            fao56_inputs=request.fao56_water_inputs,
            crop_requirement=top_crop_req,
        )

        # 8. Evaluate Satellite Context
        satellite_context: SatelliteEnvironmentalContext | None = None
        if satellite is not None:
            win_str = f"{satellite.start_date} to {satellite.end_date}"
            summary_msg = (
                f"Sentinel-2 observation ({win_str}, radius {satellite.radius_m}m) indicates "
                f"median NDVI={satellite.ndvi_median if satellite.ndvi_median is not None else 'N/A'} (canopy greenness), "
                f"NDWI={satellite.ndwi_median if satellite.ndwi_median is not None else 'N/A'} (water index), and "
                f"NDMI={satellite.ndmi_median if satellite.ndmi_median is not None else 'N/A'} (moisture stress)."
            )
            satellite_context = SatelliteEnvironmentalContext(
                available=True,
                observation_window=win_str,
                usable_observations=satellite.usable_observations,
                ndvi_median=satellite.ndvi_median,
                ndwi_median=satellite.ndwi_median,
                ndmi_median=satellite.ndmi_median,
                summary=summary_msg,
            )
        else:
            satellite_context = SatelliteEnvironmentalContext(
                available=False,
                summary="Sentinel-2 remote sensing observations were not provided or retrieved.",
            )

        # 9. Compile Data Quality Audit
        sorted_risk_flags = sorted(list(all_risk_flags))
        all_warnings = list(rec_response.data_quality.warnings) + staleness_warnings

        data_quality = DataQualityAudit(
            model_available=rec_response.data_quality.model_available,
            weather_available=weather is not None,
            satellite_available=satellite is not None,
            soil_available=soil is not None,
            missing_sources=rec_response.data_quality.missing_sources,
            stale_sources=stale_sources,
            risk_flags=sorted_risk_flags,
            warnings=all_warnings,
        )

        # 10. Generate Explanations and Limitations
        explanations = generate_advisory_explanations(
            crop_advisories=crop_advisories,
            water_advisory=water_advisory,
            satellite_context=satellite_context,
            data_quality=data_quality,
        )

        limitations = generate_advisory_limitations(
            crop_advisories=crop_advisories,
            data_quality=data_quality,
        )

        # 11. Assemble Final Farm Advisory Response
        return FarmAdvisoryResponse(
            latitude=lat,
            longitude=lon,
            observation_date=obs_date,
            crop_advisories=crop_advisories,
            water_advisory=water_advisory,
            satellite_context=satellite_context,
            risk_flags=sorted_risk_flags,
            environmental_context=rec_response.environmental_context,
            data_quality=data_quality,
            explanations=explanations,
            limitations=limitations,
            disclaimer=ADVISORY_DISCLAIMER,
        )


# Global singleton instance
farm_advisory_service = FarmAdvisoryService()
