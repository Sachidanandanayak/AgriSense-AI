"""Source normalization layer for multi-source environmental and agricultural data.

Normalizes responses from individual domain services (Weather, Satellite, Soil, Agricultural)
into standardized feature models without altering source provider business logic or fabricating values.
"""

from __future__ import annotations

from typing import Any
from app.schemas.weather import WeatherResponse
from app.schemas.satellite import SatelliteResponse
from app.schemas.soil import SoilResponse
from app.services.feature_engineering.schemas import (
    AgriculturalFeatures,
    WeatherFeatures,
    SatelliteFeatures,
    SoilFeatures,
)


def normalize_weather_response(weather: WeatherResponse | dict[str, Any] | None) -> WeatherFeatures:
    """Normalize a WeatherResponse or raw weather dictionary into WeatherFeatures.

    Args:
        weather: WeatherResponse object or dictionary with meteorological attributes.

    Returns:
        Normalized WeatherFeatures instance.
    """
    if weather is None:
        return WeatherFeatures()

    if isinstance(weather, WeatherResponse):
        return WeatherFeatures(
            weather_temperature=weather.temperature_c,
            weather_humidity=weather.humidity_percent,
            weather_precipitation=weather.rainfall_mm,
            weather_wind_speed=weather.wind_speed_mps,
            weather_timestamp=weather.weather_timestamp,
        )

    if isinstance(weather, dict):
        return WeatherFeatures(
            weather_temperature=weather.get("temperature_c") or weather.get("weather_temperature"),
            weather_humidity=weather.get("humidity_percent") or weather.get("weather_humidity"),
            weather_precipitation=weather.get("rainfall_mm") or weather.get("weather_precipitation"),
            weather_wind_speed=weather.get("wind_speed_mps") or weather.get("weather_wind_speed"),
            weather_timestamp=weather.get("weather_timestamp"),
        )

    raise TypeError(f"Expected WeatherResponse or dict, got {type(weather).__name__}")


def normalize_satellite_response(satellite: SatelliteResponse | dict[str, Any] | None) -> SatelliteFeatures:
    """Normalize a SatelliteResponse or satellite dictionary into SatelliteFeatures.

    Args:
        satellite: SatelliteResponse object or dictionary with Sentinel-2 attributes.

    Returns:
        Normalized SatelliteFeatures instance.
    """
    if satellite is None:
        return SatelliteFeatures()

    if isinstance(satellite, SatelliteResponse):
        return SatelliteFeatures(
            satellite_ndvi=satellite.ndvi_median,
            satellite_ndwi=satellite.ndwi_median,
            satellite_ndmi=satellite.ndmi_median,
            satellite_usable_observations=satellite.usable_observations,
            satellite_cloud_probability_threshold=satellite.cloud_probability_threshold,
            satellite_start_date=satellite.start_date,
            satellite_end_date=satellite.end_date,
            satellite_radius_m=satellite.radius_m,
        )

    if isinstance(satellite, dict):
        return SatelliteFeatures(
            satellite_ndvi=satellite.get("ndvi_median") or satellite.get("satellite_ndvi"),
            satellite_ndwi=satellite.get("ndwi_median") or satellite.get("satellite_ndwi"),
            satellite_ndmi=satellite.get("ndmi_median") or satellite.get("satellite_ndmi"),
            satellite_usable_observations=(
                satellite.get("usable_observations")
                if "usable_observations" in satellite
                else satellite.get("satellite_usable_observations")
            ),
            satellite_cloud_probability_threshold=(
                satellite.get("cloud_probability_threshold")
                if "cloud_probability_threshold" in satellite
                else satellite.get("satellite_cloud_probability_threshold")
            ),
            satellite_start_date=satellite.get("start_date") or satellite.get("satellite_start_date"),
            satellite_end_date=satellite.get("end_date") or satellite.get("satellite_end_date"),
            satellite_radius_m=satellite.get("radius_m") or satellite.get("satellite_radius_m"),
        )

    raise TypeError(f"Expected SatelliteResponse or dict, got {type(satellite).__name__}")


def normalize_soil_response(soil: SoilResponse | dict[str, Any] | None) -> SoilFeatures:
    """Normalize a SoilResponse or SoilGrids dictionary into SoilFeatures.

    Args:
        soil: SoilResponse object or dictionary with soil properties.

    Returns:
        Normalized SoilFeatures instance.
    """
    if soil is None:
        return SoilFeatures()

    if isinstance(soil, SoilResponse):
        return SoilFeatures(
            soil_ph=soil.soil.ph,
            soil_clay_pct=soil.soil.clay_pct,
            soil_sand_pct=soil.soil.sand_pct,
            soil_silt_pct=soil.soil.silt_pct,
            soil_organic_carbon_g_kg=soil.soil.organic_carbon_g_kg,
            soil_bulk_density=soil.soil.bulk_density,
            soil_cec=soil.soil.cec,
            soil_nitrogen_g_kg=soil.soil.nitrogen_g_kg,
            soil_depth_interval=soil.depth_interval,
            soil_resolution_m=soil.resolution_m,
        )

    if isinstance(soil, dict):
        # Handle either nested {"soil": {...}} structure or flat feature dict
        nested_props = soil.get("soil") if isinstance(soil.get("soil"), dict) else {}
        return SoilFeatures(
            soil_ph=nested_props.get("ph") or soil.get("soil_ph") or soil.get("ph"),
            soil_clay_pct=nested_props.get("clay_pct") or soil.get("soil_clay_pct") or soil.get("clay_pct"),
            soil_sand_pct=nested_props.get("sand_pct") or soil.get("soil_sand_pct") or soil.get("sand_pct"),
            soil_silt_pct=nested_props.get("silt_pct") or soil.get("soil_silt_pct") or soil.get("silt_pct"),
            soil_organic_carbon_g_kg=(
                nested_props.get("organic_carbon_g_kg")
                or soil.get("soil_organic_carbon_g_kg")
                or soil.get("organic_carbon_g_kg")
            ),
            soil_bulk_density=(
                nested_props.get("bulk_density")
                or soil.get("soil_bulk_density")
                or soil.get("bulk_density")
            ),
            soil_cec=nested_props.get("cec") or soil.get("soil_cec") or soil.get("cec"),
            soil_nitrogen_g_kg=(
                nested_props.get("nitrogen_g_kg")
                or soil.get("soil_nitrogen_g_kg")
                or soil.get("nitrogen_g_kg")
            ),
            soil_depth_interval=soil.get("depth_interval") or soil.get("soil_depth_interval"),
            soil_resolution_m=soil.get("resolution_m") or soil.get("soil_resolution_m"),
        )

    raise TypeError(f"Expected SoilResponse or dict, got {type(soil).__name__}")


def normalize_agricultural_data(agri_data: dict[str, Any] | None) -> AgriculturalFeatures:
    """Normalize raw agricultural dataset fields into AgriculturalFeatures.

    Supports both original column names ('N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall')
    and standardized long-form field names.

    Args:
        agri_data: Dictionary representing an agricultural sample.

    Returns:
        Normalized AgriculturalFeatures instance.
    """
    if agri_data is None:
        return AgriculturalFeatures()

    if not isinstance(agri_data, dict):
        raise TypeError(f"Expected dict for agricultural data, got {type(agri_data).__name__}")

    n_val = agri_data.get("N") if "N" in agri_data else agri_data.get("nitrogen")
    p_val = agri_data.get("P") if "P" in agri_data else agri_data.get("phosphorus")
    k_val = agri_data.get("K") if "K" in agri_data else agri_data.get("potassium")

    temp_val = (
        agri_data.get("temperature")
        if "temperature" in agri_data
        else agri_data.get("historical_temperature")
    )
    hum_val = (
        agri_data.get("humidity")
        if "humidity" in agri_data
        else agri_data.get("historical_humidity")
    )
    ph_val = agri_data.get("ph") if "ph" in agri_data else agri_data.get("historical_ph")
    rain_val = (
        agri_data.get("rainfall")
        if "rainfall" in agri_data
        else agri_data.get("historical_rainfall")
    )

    return AgriculturalFeatures(
        nitrogen=float(n_val) if n_val is not None else None,
        phosphorus=float(p_val) if p_val is not None else None,
        potassium=float(k_val) if k_val is not None else None,
        historical_temperature=float(temp_val) if temp_val is not None else None,
        historical_humidity=float(hum_val) if hum_val is not None else None,
        historical_ph=float(ph_val) if ph_val is not None else None,
        historical_rainfall=float(rain_val) if rain_val is not None else None,
    )
