"""Production Crop Suitability & Recommendation Service.

Orchestrates:
1. Input validation and boundary enforcement.
2. Agricultural input feature adaptation to exact 11-feature model input schema.
3. Benchmark Random Forest model inference and top-K ranked probability estimates.
4. Optional retrieval or attachment of live/cached weather, satellite, and soil data.
5. Phase 7 multi-source feature alignment and provenance tracking.
6. Transparent explanation generation and operational limitations reporting.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
from typing import Any

from app.core.config import settings
from app.schemas.satellite import SatelliteResponse
from app.schemas.soil import SoilResponse
from app.schemas.weather import WeatherResponse
from app.services.feature_engineering.builder import MultiSourceFeatureBuilder
from app.services.feature_engineering.validators import (
    SpatialAlignmentError,
    TemporalAlignmentError,
)
from app.services.recommendation.exceptions import RecommendationValidationError
from app.services.recommendation.explanation import (
    generate_explanations,
    generate_limitations,
)
from app.services.recommendation.model_adapter import (
    CropModelAdapter,
    crop_model_adapter,
)
from app.services.recommendation.schemas import (
    DataQualityReport,
    EnvironmentalContext,
    MANDATORY_DISCLAIMER,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation.validators import (
    validate_agricultural_inputs,
    validate_coordinates,
    validate_observation_date,
    validate_top_k,
)
from app.services.satellite_service import (
    SatelliteService,
    SatelliteServiceError,
    satellite_service,
)
from app.services.soil_service import (
    SoilService,
    SoilServiceError,
    soil_service,
)
from app.services.soil_provider import SoilProviderError
from app.services.weather_service import (
    WeatherService,
    WeatherServiceError,
    weather_service,
)

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service orchestrating crop suitability recommendations with environmental context."""

    def __init__(
        self,
        model_adapter: CropModelAdapter | None = None,
        feature_builder: MultiSourceFeatureBuilder | None = None,
        weather_svc: WeatherService | None = None,
        satellite_svc: SatelliteService | None = None,
        soil_svc: SoilService | None = None,
    ) -> None:
        """Initialize recommendation service with dependencies.

        Args:
            model_adapter: Adapter for benchmark crop recommendation model.
            feature_builder: Phase 7 multi-source alignment and normalization builder.
            weather_svc: Meteorological service provider.
            satellite_svc: Satellite remote sensing provider.
            soil_svc: Digital soil mapping provider.
        """
        self.model_adapter = model_adapter or crop_model_adapter
        self.feature_builder = feature_builder or MultiSourceFeatureBuilder()
        self.weather_service = weather_svc or weather_service
        self.satellite_service = satellite_svc or satellite_service
        self.soil_service = soil_svc or soil_service

    async def generate_recommendation(
        self,
        request: RecommendationRequest,
    ) -> RecommendationResponse:
        """Generate farmer-facing crop recommendations with supporting environmental context.

        Args:
            request: Validated RecommendationRequest payload.

        Returns:
            Structured RecommendationResponse.

        Raises:
            InvalidCoordinatesError: On invalid coordinate bounds.
            InvalidDateError: On malformed date format.
            MissingModelInputError: If required agricultural features are missing.
            RecommendationValidationError: On invalid parameters.
            ModelUnavailableError: If model cannot be loaded.
            ModelPredictionError: If inference execution fails.
        """
        warnings: list[str] = []

        # 1. Validate primary spatial and temporal inputs
        lat, lon = validate_coordinates(request.latitude, request.longitude)
        obs_date = validate_observation_date(request.observation_date)

        # 2. Validate agricultural inputs (strictly no silent imputation)
        agri_inputs = validate_agricultural_inputs(request.agricultural_inputs)

        # 3. Validate top-K parameter
        top_k = validate_top_k(request.top_k, max_classes=len(self.model_adapter.classes))

        # 4. Construct exact 11-feature model input vector (preserving training schema and order)
        model_features = self.model_adapter.adapt_agricultural_inputs(agri_inputs)

        # 5. Execute model inference for top-K recommendations
        recommendations = self.model_adapter.predict_top_k(model_features, k=top_k)

        # 6. Resolve Environmental Context (Weather, Satellite, Soil)
        # 6a. Weather Context
        weather: WeatherResponse | None = request.weather_context
        if weather is None and request.fetch_live_weather:
            try:
                weather = await self.weather_service.get_current_weather(lat, lon)
            except WeatherServiceError as exc:
                logger.warning("Could not retrieve live weather for (%s, %s): %s", lat, lon, exc)
                warnings.append(f"Live weather query unavailable: {exc}")
                weather = None

        # 6b. Satellite Context
        satellite: SatelliteResponse | None = request.satellite_context
        if satellite is None and request.fetch_live_satellite:
            try:
                ref_date = (
                    datetime.strptime(obs_date, "%Y-%m-%d").date()
                    if obs_date
                    else date.today()
                )
                start_d = (ref_date - timedelta(days=settings.FEATURE_SATELLITE_MAX_WINDOW_DAYS)).isoformat()
                end_d = ref_date.isoformat()
                satellite = await self.satellite_service.get_satellite_indices(
                    latitude=lat,
                    longitude=lon,
                    start_date=start_d,
                    end_date=end_d,
                )
            except SatelliteServiceError as exc:
                logger.warning("Could not retrieve live satellite indices for (%s, %s): %s", lat, lon, exc)
                warnings.append(f"Live satellite query unavailable: {exc}")
                satellite = None

        # 6c. Soil Context
        soil: SoilResponse | None = request.soil_context
        if soil is None and request.fetch_live_soil:
            try:
                soil = await self.soil_service.get_soil_data(
                    latitude=lat,
                    longitude=lon,
                    depth_interval=settings.SOIL_DEFAULT_DEPTH,
                )
            except (SoilServiceError, SoilProviderError) as exc:
                logger.warning("Could not retrieve live soil data for (%s, %s): %s", lat, lon, exc)
                warnings.append(f"Live soil query unavailable: {exc}")
                soil = None

        # 7. Multi-Source Alignment Check via Phase 7 Feature Builder
        if weather is not None or satellite is not None or soil is not None:
            try:
                # Format agricultural dictionary for feature engineering builder
                agri_dict = {
                    "nitrogen": agri_inputs.nitrogen,
                    "phosphorus": agri_inputs.phosphorus,
                    "potassium": agri_inputs.potassium,
                    "historical_temperature": agri_inputs.temperature,
                    "historical_humidity": agri_inputs.humidity,
                    "historical_ph": agri_inputs.ph,
                    "historical_rainfall": agri_inputs.rainfall,
                }
                self.feature_builder.build_unified_observation(
                    latitude=lat,
                    longitude=lon,
                    observation_date=obs_date,
                    weather=weather,
                    satellite=satellite,
                    soil=soil,
                    agricultural_data=agri_dict,
                    strict_spatial=True,
                    strict_temporal=obs_date is not None,
                )
            except (SpatialAlignmentError, TemporalAlignmentError) as exc:
                logger.warning("Multi-source alignment failure: %s", exc)
                raise RecommendationValidationError(
                    f"Environmental context alignment failure: {exc}"
                ) from exc

        # 8. Compile Data Quality and Provenance Report
        weather_avail = weather is not None
        satellite_avail = satellite is not None
        soil_avail = soil is not None

        missing_sources: list[str] = []
        if not weather_avail:
            missing_sources.append("weather")
        if not satellite_avail:
            missing_sources.append("satellite")
        if not soil_avail:
            missing_sources.append("soil")

        data_quality = DataQualityReport(
            model_available=True,
            model_version="crop_recommendation_rf_v1",
            weather_available=weather_avail,
            satellite_available=satellite_avail,
            soil_available=soil_avail,
            missing_sources=missing_sources,
            warnings=warnings,
        )

        # 9. Generate Transparent Explanations and Limitations
        explanations = generate_explanations(
            recommendations=recommendations,
            agricultural_inputs=agri_inputs,
            weather=weather,
            satellite=satellite,
            soil=soil,
        )

        limitations = generate_limitations(
            weather_available=weather_avail,
            satellite_available=satellite_avail,
            soil_available=soil_avail,
        )

        # 10. Assemble Final Structured Response
        return RecommendationResponse(
            latitude=lat,
            longitude=lon,
            observation_date=obs_date,
            recommendations=recommendations,
            environmental_context=EnvironmentalContext(
                weather=weather,
                satellite=satellite,
                soil=soil,
            ),
            data_quality=data_quality,
            explanation=explanations,
            limitations=limitations,
            model_input_features=model_features,
            disclaimer=MANDATORY_DISCLAIMER,
        )


# Global singleton instance for application reuse
recommendation_service = RecommendationService()
