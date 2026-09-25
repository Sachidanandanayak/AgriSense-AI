"""Weather data integration service for AgriSense AI.

Interfaces with external meteorological providers (Open-Meteo),
handles network resiliency and timeouts, and normalizes raw observations
into the standardized application schema.
"""

from __future__ import annotations
import logging
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.weather import WeatherResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Weather Exceptions
# ---------------------------------------------------------------------------

class WeatherServiceError(Exception):
    """Base exception for all weather service errors."""


class InvalidCoordinatesError(WeatherServiceError):
    """Raised when latitude or longitude coordinates fall outside valid geographic bounds."""


class WeatherTimeoutError(WeatherServiceError):
    """Raised when an external weather provider request exceeds the timeout threshold."""


class WeatherConnectionError(WeatherServiceError):
    """Raised when network connectivity to the weather provider fails."""


class WeatherRateLimitError(WeatherServiceError):
    """Raised when external weather provider rate limits are exceeded."""


class WeatherProviderError(WeatherServiceError):
    """Raised when the weather provider returns an unexpected or error response."""


# ---------------------------------------------------------------------------
# Coordinate Validation Helper
# ---------------------------------------------------------------------------

def validate_coordinates(latitude: float, longitude: float) -> None:
    """Validate geographic coordinates within physical decimal degree limits.

    Args:
        latitude: Latitude between -90.0 and 90.0 degrees.
        longitude: Longitude between -180.0 and 180.0 degrees.

    Raises:
        InvalidCoordinatesError: If coordinates are out of bounds or non-numeric.
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (ValueError, TypeError) as exc:
        raise InvalidCoordinatesError(
            f"Coordinates must be valid numbers: latitude={latitude}, longitude={longitude}"
        ) from exc

    if not (-90.0 <= lat <= 90.0):
        raise InvalidCoordinatesError(
            f"Invalid latitude {lat}. Latitude must be between -90.0 and 90.0 degrees."
        )

    if not (-180.0 <= lon <= 180.0):
        raise InvalidCoordinatesError(
            f"Invalid longitude {lon}. Longitude must be between -180.0 and 180.0 degrees."
        )


# ---------------------------------------------------------------------------
# Weather Service Implementation
# ---------------------------------------------------------------------------

class WeatherService:
    """Service to fetch and normalize weather data from meteorological providers."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = base_url or settings.WEATHER_BASE_URL
        self.api_key = api_key or settings.WEATHER_API_KEY
        self.timeout = (
            timeout if timeout is not None else settings.WEATHER_TIMEOUT_SECONDS
        )

    async def fetch_weather_raw(
        self,
        latitude: float,
        longitude: float,
        client: httpx.AsyncClient | None = None,
    ) -> dict[str, Any]:
        """Fetch raw weather payload from the provider API.

        Args:
            latitude: Validated latitude.
            longitude: Validated longitude.
            client: Optional httpx.AsyncClient for dependency injection/testing.

        Returns:
            Dictionary representing the raw provider JSON response.

        Raises:
            WeatherTimeoutError: If the upstream call times out.
            WeatherConnectionError: If network connection fails.
            WeatherRateLimitError: If rate limit is encountered (HTTP 429).
            WeatherProviderError: For upstream HTTP errors or invalid response payloads.
        """
        params: dict[str, Any] = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m",
            "wind_speed_unit": "ms",
        }

        if self.api_key:
            params["apikey"] = self.api_key

        owns_client = client is None
        async_client = client or httpx.AsyncClient(timeout=self.timeout)

        try:
            response = await async_client.get(self.base_url, params=params)

            if response.status_code == 429:
                logger.warning("Weather provider rate limit exceeded (HTTP 429).")
                raise WeatherRateLimitError(
                    "Weather provider rate limit exceeded. Please try again later."
                )

            if response.is_client_error or response.is_server_error:
                logger.error(
                    "Weather provider returned error status %s: %s",
                    response.status_code,
                    response.text[:200],
                )
                raise WeatherProviderError(
                    f"Weather provider error (HTTP {response.status_code})."
                )

            try:
                data = response.json()
            except Exception as exc:
                logger.error("Failed to parse JSON response from weather provider: %s", exc)
                raise WeatherProviderError(
                    "Weather provider returned an invalid non-JSON response."
                ) from exc

            if not isinstance(data, dict):
                raise WeatherProviderError(
                    "Weather provider response payload must be a JSON object."
                )

            return data

        except httpx.TimeoutException as exc:
            logger.error("Weather provider request timed out: %s", exc)
            raise WeatherTimeoutError(
                "Weather provider request timed out."
            ) from exc
        except httpx.NetworkError as exc:
            logger.error("Weather provider network connection failed: %s", exc)
            raise WeatherConnectionError(
                "Unable to connect to the weather provider."
            ) from exc
        finally:
            if owns_client:
                await async_client.aclose()

    def normalize_weather_data(
        self,
        raw_data: dict[str, Any],
        latitude: float,
        longitude: float,
    ) -> WeatherResponse:
        """Normalize raw provider data into the AgriSense AI standard weather schema.

        Args:
            raw_data: Raw JSON payload from the weather provider.
            latitude: Requested query latitude.
            longitude: Requested query longitude.

        Returns:
            Validated WeatherResponse Pydantic model instance.

        Raises:
            WeatherProviderError: If expected fields are missing or fail schema validation.
        """
        current = raw_data.get("current")
        if not isinstance(current, dict):
            raise WeatherProviderError(
                "Weather provider response missing 'current' weather block."
            )

        # Check required raw fields
        for field in ("temperature_2m", "relative_humidity_2m", "wind_speed_10m", "time"):
            if field not in current or current[field] is None:
                raise WeatherProviderError(
                    f"Weather provider payload missing required observation field: '{field}'"
                )

        # Precipitation fallback: check 'precipitation' first, then 'rain', default 0.0
        rainfall = current.get("precipitation")
        if rainfall is None:
            rainfall = current.get("rain", 0.0)

        try:
            rainfall_val = float(rainfall)
        except (ValueError, TypeError):
            rainfall_val = 0.0

        try:
            return WeatherResponse(
                latitude=round(latitude, 4),
                longitude=round(longitude, 4),
                temperature_c=float(current["temperature_2m"]),
                humidity_percent=float(current["relative_humidity_2m"]),
                rainfall_mm=max(0.0, rainfall_val),
                wind_speed_mps=float(current["wind_speed_10m"]),
                weather_timestamp=str(current["time"]),
            )
        except (ValidationError, ValueError, TypeError) as exc:
            logger.error("Failed to construct validated WeatherResponse: %s", exc)
            raise WeatherProviderError(
                f"Weather normalization validation failed: {exc}"
            ) from exc

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
        client: httpx.AsyncClient | None = None,
    ) -> WeatherResponse:
        """Retrieve and normalize current weather for the given coordinates.

        Args:
            latitude: Latitude in decimal degrees (-90 to 90).
            longitude: Longitude in decimal degrees (-180 to 180).
            client: Optional httpx.AsyncClient.

        Returns:
            Normalized WeatherResponse.

        Raises:
            InvalidCoordinatesError: If coordinates are out of bounds.
            WeatherTimeoutError: If the external call times out.
            WeatherConnectionError: If network connection fails.
            WeatherRateLimitError: If provider rate limits are exceeded.
            WeatherProviderError: If the provider returns an error or invalid payload.
        """
        validate_coordinates(latitude, longitude)
        raw_data = await self.fetch_weather_raw(latitude, longitude, client=client)
        return self.normalize_weather_data(raw_data, latitude, longitude)


# Default singleton instance for app-wide dependency injection
weather_service = WeatherService()
