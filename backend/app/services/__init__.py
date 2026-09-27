"""Business logic and external integration services for AgriSense AI."""

from app.services.weather_service import (
    WeatherService,
    weather_service,
    WeatherServiceError,
    InvalidCoordinatesError,
    WeatherTimeoutError,
    WeatherConnectionError,
    WeatherRateLimitError,
    WeatherProviderError,
)
from app.services.satellite_service import (
    SatelliteService,
    satellite_service,
    SatelliteServiceError,
    InvalidDateRangeError,
    InvalidParameterError,
    EarthEngineAuthError,
    EarthEngineInitError,
    NoObservationsFoundError,
    EarthEngineExecutionError,
    compute_ndvi,
    compute_ndwi,
    compute_ndmi,
)

__all__ = [
    "WeatherService",
    "weather_service",
    "WeatherServiceError",
    "InvalidCoordinatesError",
    "WeatherTimeoutError",
    "WeatherConnectionError",
    "WeatherRateLimitError",
    "WeatherProviderError",
    "SatelliteService",
    "satellite_service",
    "SatelliteServiceError",
    "InvalidDateRangeError",
    "InvalidParameterError",
    "EarthEngineAuthError",
    "EarthEngineInitError",
    "NoObservationsFoundError",
    "EarthEngineExecutionError",
    "compute_ndvi",
    "compute_ndwi",
    "compute_ndmi",
]
