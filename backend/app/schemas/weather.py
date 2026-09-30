"""Pydantic schemas for weather data validation and response serialization."""

from pydantic import BaseModel, Field, ConfigDict


class WeatherResponse(BaseModel):
    """Normalized weather data schema representing localized meteorological observations."""

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees (-90.0 to 90.0)",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees (-180.0 to 180.0)",
    )
    temperature_c: float = Field(
        ...,
        ge=-100.0,
        le=70.0,
        description="Air temperature in degrees Celsius (2m above ground)",
    )
    humidity_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Relative humidity percentage (0.0% to 100.0%)",
    )
    rainfall_mm: float = Field(
        ...,
        ge=0.0,
        description="Precipitation / rainfall in millimeters (non-negative)",
    )
    wind_speed_mps: float = Field(
        ...,
        ge=0.0,
        description="Wind speed in meters per second (10m above ground)",
    )
    weather_timestamp: str = Field(
        ...,
        min_length=1,
        description="ISO 8601 formatted timestamp of the weather observation",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "latitude": 16.20,
                "longitude": 77.35,
                "temperature_c": 28.4,
                "humidity_percent": 64.0,
                "rainfall_mm": 0.0,
                "wind_speed_mps": 3.2,
                "weather_timestamp": "2026-09-25T17:15",
            }
        }
    )
