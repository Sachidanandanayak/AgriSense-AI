"""Explanation and limitation generation layer for recommendation engine.

Produces transparent, data-grounded explanations based strictly on available
environmental observations. Strictly enforces scientific integrity rules:
- Prohibits claiming model probability is "suitability percentage" or "yield probability".
- Prohibits claiming satellite NDVI/NDWI/NDMI directly proves crop suitability.
- Explicitly states missing data sources and operational limitations.
"""

from __future__ import annotations

from typing import Any
from app.schemas.satellite import SatelliteResponse
from app.schemas.soil import SoilResponse
from app.schemas.weather import WeatherResponse
from app.services.recommendation.schemas import (
    CropRecommendationItem,
    MANDATORY_DISCLAIMER,
)


def generate_explanations(
    recommendations: list[CropRecommendationItem],
    agricultural_inputs: dict[str, float] | Any,
    weather: WeatherResponse | None = None,
    satellite: SatelliteResponse | None = None,
    soil: SoilResponse | None = None,
) -> list[str]:
    """Generate transparent, evidence-grounded explanatory notes for the farmer.

    Args:
        recommendations: Ranked recommendations with model probability estimates.
        agricultural_inputs: Agricultural/nutrient inputs used for prediction.
        weather: Optional WeatherResponse object.
        satellite: Optional SatelliteResponse object.
        soil: Optional SoilResponse object.

    Returns:
        List of explanatory sentences based strictly on observed data.
    """
    explanations: list[str] = []

    # 1. Primary Recommendation Explanation
    if recommendations:
        top_crop = recommendations[0]
        def _get_val(key: str) -> str:
            if isinstance(agricultural_inputs, dict):
                v = agricultural_inputs.get(key)
            else:
                v = getattr(agricultural_inputs, key, None)
            return f"{v}" if v is not None else "N/A"

        n = _get_val("nitrogen") or _get_val("N")
        p = _get_val("phosphorus") or _get_val("P")
        k = _get_val("potassium") or _get_val("K")
        ph = _get_val("ph")
        temp = _get_val("temperature")
        rain = _get_val("rainfall")

        explanations.append(
            f"The benchmark Random Forest model ranked '{top_crop.crop}' highest "
            f"(benchmark-model confidence estimate: {top_crop.confidence_percentage}) "
            f"for the supplied agricultural inputs (N={n} kg/ha, P={p} kg/ha, K={k} kg/ha, "
            f"pH={ph}, temperature={temp}°C, rainfall={rain} mm)."
        )

        # Secondary recommendations summary
        if len(recommendations) > 1:
            others = [f"'{r.crop}' ({r.confidence_percentage})" for r in recommendations[1:]]
            explanations.append(
                f"Secondary model-ranked alternatives: {', '.join(others)}."
            )

    # 2. Weather Context Explanation
    if weather is not None:
        explanations.append(
            f"Current meteorological context: {weather.temperature_c}°C air temperature, "
            f"{weather.humidity_percent}% relative humidity, {weather.rainfall_mm} mm precipitation, "
            f"and {weather.wind_speed_mps} m/s wind speed at the target coordinates."
        )
    else:
        explanations.append(
            "Weather data was unavailable; the recommendation was not enriched with current weather context."
        )

    # 3. Satellite Context Explanation
    if satellite is not None:
        date_range = (
            f"({satellite.start_date} to {satellite.end_date})"
            if satellite.start_date and satellite.end_date
            else ""
        )
        explanations.append(
            f"Sentinel-2 satellite observation {date_range} indicates median NDVI of {satellite.ndvi_median:.2f}, "
            f"NDWI of {satellite.ndwi_median:.2f}, and NDMI of {satellite.ndmi_median:.2f} within a "
            f"{int(satellite.radius_m)}m radius. These indices serve as contextual environmental indicators "
            f"of current canopy vigor and moisture, not direct proof of crop suitability."
        )
    else:
        explanations.append(
            "Satellite observations were unavailable; recent spectral vegetation and moisture indicators were not evaluated."
        )

    # 4. Soil Context Explanation
    if soil is not None and soil.soil is not None:
        s = soil.soil
        explanations.append(
            f"Digital soil mapping from ISRIC SoilGrids 2.0 at {soil.depth_interval} depth indicates "
            f"soil pH {s.ph}, clay {s.clay_pct}%, sand {s.sand_pct}%, and "
            f"organic carbon {s.organic_carbon_g_kg} g/kg."
        )
    else:
        explanations.append(
            "Soil data was unavailable; the recommendation was not enriched with digital soil mapping properties."
        )

    return explanations


def generate_limitations(
    weather_available: bool,
    satellite_available: bool,
    soil_available: bool,
) -> list[str]:
    """Generate explicit scientific and operational limitations for the advisory response.

    Args:
        weather_available: Whether live weather context was retrieved.
        satellite_available: Whether Sentinel-2 satellite context was retrieved.
        soil_available: Whether ISRIC SoilGrids context was retrieved.

    Returns:
        List of limitation statements clearly warning the user of system boundaries.
    """
    limitations: list[str] = [
        MANDATORY_DISCLAIMER,
        (
            "Benchmark Model Scope: The existing classifier was trained on a 2,200-sample benchmark "
            "agricultural dataset under controlled trial conditions. Model probability estimates reflect "
            "classification likelihood across benchmark feature boundaries, NOT a guaranteed probability "
            "of successful harvest or commercial yield."
        ),
        (
            "Environmental Context Function: Satellite remote sensing (NDVI, NDWI, NDMI) and meteorological "
            "feeds provide real-time environmental context. They do not constitute scientific proof of biological "
            "crop suitability or disease immunity."
        ),
        (
            "Digital Soil Mapping Resolution: ISRIC SoilGrids 2.0 predictions represent 250m grid-scale spatial "
            "estimates. They do not replace certified on-farm laboratory soil testing."
        ),
        (
            "Unmodelled Agronomic Risks: Field microclimates, frost pockets, pest and disease vectors, "
            "weed competition, seed variety differences, irrigation infrastructure, and market economic dynamics "
            "are not accounted for in this recommendation."
        ),
    ]

    # Specific missing data limitations
    if not weather_available:
        limitations.append(
            "Missing Weather Context: Real-time temperature, moisture, and rainfall risks could not be verified."
        )
    if not satellite_available:
        limitations.append(
            "Missing Satellite Context: Current canopy greenness and surface moisture trends were not verified."
        )
    if not soil_available:
        limitations.append(
            "Missing Soil Context: Soil physical texture (clay/sand/silt) and organic matter were not verified."
        )

    return limitations
