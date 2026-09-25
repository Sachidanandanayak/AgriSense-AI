"""Comprehensive unit and API tests for AgriSense AI weather data integration.

All unit tests are fully isolated and mock external HTTP responses to ensure
deterministic execution without external network dependencies.
"""

from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import httpx
from pydantic import ValidationError

from app.main import app
from app.schemas.weather import WeatherResponse
from app.services.weather_service import (
    WeatherService,
    InvalidCoordinatesError,
    WeatherTimeoutError,
    WeatherConnectionError,
    WeatherRateLimitError,
    WeatherProviderError,
    validate_coordinates,
)


# Authentic mock payload matching Open-Meteo API response structure
SAMPLE_OPEN_METEO_PAYLOAD = {
    "latitude": 16.203865,
    "longitude": 77.36243,
    "generationtime_ms": 2.53,
    "utc_offset_seconds": 0,
    "timezone": "GMT",
    "timezone_abbreviation": "GMT",
    "elevation": 415.0,
    "current_units": {
        "time": "iso8601",
        "interval": "seconds",
        "temperature_2m": "°C",
        "relative_humidity_2m": "%",
        "precipitation": "mm",
        "rain": "mm",
        "wind_speed_10m": "m/s",
    },
    "current": {
        "time": "2026-09-25T17:15",
        "interval": 900,
        "temperature_2m": 28.4,
        "relative_humidity_2m": 64.0,
        "precipitation": 0.0,
        "rain": 0.0,
        "wind_speed_10m": 3.2,
    },
}


class TestWeatherServiceUnit(unittest.IsolatedAsyncioTestCase):
    """Unit tests for WeatherService business logic, validation, and normalization."""

    def setUp(self):
        self.service = WeatherService(
            base_url="https://api.open-meteo.com/v1/forecast",
            api_key=None,
            timeout=5.0,
        )

    # 1. Successful weather response
    async def test_01_successful_weather_response(self):
        """1. Verify successful weather retrieval and normalization."""
        mock_response = httpx.Response(
            status_code=200,
            json=SAMPLE_OPEN_METEO_PAYLOAD,
            request=httpx.Request("GET", "https://api.open-meteo.com/v1/forecast"),
        )
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await self.service.get_current_weather(
            latitude=16.20, longitude=77.35, client=mock_client
        )

        self.assertIsInstance(result, WeatherResponse)
        self.assertEqual(result.latitude, 16.20)
        self.assertEqual(result.longitude, 77.35)
        self.assertEqual(result.temperature_c, 28.4)
        self.assertEqual(result.humidity_percent, 64.0)
        self.assertEqual(result.rainfall_mm, 0.0)
        self.assertEqual(result.wind_speed_mps, 3.2)
        self.assertEqual(result.weather_timestamp, "2026-09-25T17:15")

    # 2. Invalid latitude
    def test_02_invalid_latitude_bounds(self):
        """2. Verify out-of-bounds latitude raises InvalidCoordinatesError."""
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(latitude=91.0, longitude=50.0)

        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(latitude=-90.1, longitude=50.0)

        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(latitude="invalid", longitude=50.0)

    # 3. Invalid longitude
    def test_03_invalid_longitude_bounds(self):
        """3. Verify out-of-bounds longitude raises InvalidCoordinatesError."""
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(latitude=20.0, longitude=180.5)

        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(latitude=20.0, longitude=-181.0)

        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(latitude=20.0, longitude="not-a-number")

    # 4. API timeout
    async def test_04_api_timeout(self):
        """4. Verify external API timeout raises WeatherTimeoutError."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))

        with self.assertRaises(WeatherTimeoutError):
            await self.service.get_current_weather(
                latitude=16.20, longitude=77.35, client=mock_client
            )

    # 5. API HTTP failure
    async def test_05_api_http_failure(self):
        """5. Verify HTTP 500 error from provider raises WeatherProviderError."""
        mock_response = httpx.Response(
            status_code=500,
            text="Internal Server Error",
            request=httpx.Request("GET", "https://api.open-meteo.com/v1/forecast"),
        )
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with self.assertRaises(WeatherProviderError):
            await self.service.get_current_weather(
                latitude=16.20, longitude=77.35, client=mock_client
            )

    # Rate limiting
    async def test_06_api_rate_limiting(self):
        """Verify HTTP 429 rate limit raises WeatherRateLimitError."""
        mock_response = httpx.Response(
            status_code=429,
            text="Too Many Requests",
            request=httpx.Request("GET", "https://api.open-meteo.com/v1/forecast"),
        )
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with self.assertRaises(WeatherRateLimitError):
            await self.service.get_current_weather(
                latitude=16.20, longitude=77.35, client=mock_client
            )

    # Network failure
    async def test_07_api_network_failure(self):
        """Verify network connection failure raises WeatherConnectionError."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

        with self.assertRaises(WeatherConnectionError):
            await self.service.get_current_weather(
                latitude=16.20, longitude=77.35, client=mock_client
            )

    # 6. Missing weather fields
    def test_08_missing_weather_fields(self):
        """6. Verify missing fields in provider response raise WeatherProviderError."""
        # Missing 'current' block
        with self.assertRaises(WeatherProviderError):
            self.service.normalize_weather_data({"latitude": 16.2}, 16.2, 77.35)

        # Missing 'temperature_2m'
        incomplete_payload = {
            "current": {
                "time": "2026-09-25T17:15",
                "relative_humidity_2m": 60,
                "wind_speed_10m": 3.0,
            }
        }
        with self.assertRaises(WeatherProviderError):
            self.service.normalize_weather_data(incomplete_payload, 16.2, 77.35)

    # 7. Correct normalization & rainfall fallback
    def test_09_correct_normalization_and_rain_fallback(self):
        """7. Verify normalization correctly falls back from precipitation to rain."""
        payload_with_rain_only = {
            "current": {
                "time": "2026-09-25T18:00",
                "temperature_2m": 25.5,
                "relative_humidity_2m": 80.0,
                "rain": 12.4,
                "wind_speed_10m": 4.5,
            }
        }
        res = self.service.normalize_weather_data(payload_with_rain_only, 16.20123, 77.35123)
        self.assertEqual(res.rainfall_mm, 12.4)
        self.assertEqual(res.latitude, 16.2012)
        self.assertEqual(res.longitude, 77.3512)

    # 8. Correct units
    def test_10_correct_units(self):
        """8. Verify all fields adhere strictly to documented SI/agronomic units."""
        payload = {
            "current": {
                "time": "2026-09-25T12:00",
                "temperature_2m": 32.1,      # Celsius
                "relative_humidity_2m": 45.0,  # %
                "precipitation": 2.5,         # mm
                "wind_speed_10m": 5.1,        # m/s
            }
        }
        normalized = self.service.normalize_weather_data(payload, 20.0, 75.0)
        self.assertIsInstance(normalized.temperature_c, float)
        self.assertIsInstance(normalized.humidity_percent, float)
        self.assertIsInstance(normalized.rainfall_mm, float)
        self.assertIsInstance(normalized.wind_speed_mps, float)
        self.assertGreaterEqual(normalized.humidity_percent, 0.0)
        self.assertLessEqual(normalized.humidity_percent, 100.0)
        self.assertGreaterEqual(normalized.rainfall_mm, 0.0)
        self.assertGreaterEqual(normalized.wind_speed_mps, 0.0)


class TestWeatherSchemaValidation(unittest.TestCase):
    """9. Unit tests for Pydantic WeatherResponse schema validation rules."""

    def test_valid_schema(self):
        """Verify WeatherResponse accepts valid values."""
        item = WeatherResponse(
            latitude=16.20,
            longitude=77.35,
            temperature_c=28.4,
            humidity_percent=64.0,
            rainfall_mm=0.0,
            wind_speed_mps=3.2,
            weather_timestamp="2026-09-25T17:15",
        )
        self.assertEqual(item.latitude, 16.20)
        self.assertEqual(item.temperature_c, 28.4)

    def test_invalid_latitude_schema(self):
        """Verify WeatherResponse rejects latitude out of bounds."""
        with self.assertRaises(ValidationError):
            WeatherResponse(
                latitude=95.0,
                longitude=77.35,
                temperature_c=28.4,
                humidity_percent=64.0,
                rainfall_mm=0.0,
                wind_speed_mps=3.2,
                weather_timestamp="2026-09-25T17:15",
            )

    def test_invalid_humidity_schema(self):
        """Verify WeatherResponse rejects humidity > 100 or < 0."""
        with self.assertRaises(ValidationError):
            WeatherResponse(
                latitude=16.20,
                longitude=77.35,
                temperature_c=28.4,
                humidity_percent=105.0,
                rainfall_mm=0.0,
                wind_speed_mps=3.2,
                weather_timestamp="2026-09-25T17:15",
            )

    def test_negative_rainfall_schema(self):
        """Verify WeatherResponse rejects negative rainfall."""
        with self.assertRaises(ValidationError):
            WeatherResponse(
                latitude=16.20,
                longitude=77.35,
                temperature_c=28.4,
                humidity_percent=50.0,
                rainfall_mm=-5.0,
                wind_speed_mps=3.2,
                weather_timestamp="2026-09-25T17:15",
            )

    def test_negative_wind_speed_schema(self):
        """Verify WeatherResponse rejects negative wind speed."""
        with self.assertRaises(ValidationError):
            WeatherResponse(
                latitude=16.20,
                longitude=77.35,
                temperature_c=28.4,
                humidity_percent=50.0,
                rainfall_mm=0.0,
                wind_speed_mps=-1.5,
                weather_timestamp="2026-09-25T17:15",
            )


class TestWeatherApiEndpoints(unittest.IsolatedAsyncioTestCase):
    """Integration and HTTP level tests for API endpoints using FastAPI ASGI client."""

    async def asyncSetUp(self):
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose()

    # Test GET /
    async def test_existing_root_endpoint(self):
        """Verify GET / continues to return welcome message."""
        response = await self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to AgriSense AI API"})

    # Test GET /health
    async def test_existing_health_endpoint(self):
        """Verify GET /health continues to return healthy status."""
        response = await self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    # Test GET /docs
    async def test_existing_docs_endpoint(self):
        """Verify Swagger UI GET /docs continues to function."""
        response = await self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))

    # Test GET /api/weather with mocked successful service
    async def test_api_weather_success(self):
        """Verify GET /api/weather returns normalized weather response on success."""
        mock_result = WeatherResponse(
            latitude=16.20,
            longitude=77.35,
            temperature_c=28.4,
            humidity_percent=64.0,
            rainfall_mm=0.0,
            wind_speed_mps=3.2,
            weather_timestamp="2026-09-25T17:15",
        )
        with patch(
            "app.api.routes.weather.weather_service.get_current_weather",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = mock_result

            response = await self.client.get("/api/weather?latitude=16.20&longitude=77.35")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["latitude"], 16.20)
            self.assertEqual(data["longitude"], 77.35)
            self.assertEqual(data["temperature_c"], 28.4)
            self.assertEqual(data["humidity_percent"], 64.0)
            self.assertEqual(data["rainfall_mm"], 0.0)
            self.assertEqual(data["wind_speed_mps"], 3.2)
            self.assertEqual(data["weather_timestamp"], "2026-09-25T17:15")

    # Test GET /api/weather with invalid latitude
    async def test_api_weather_invalid_latitude(self):
        """Verify GET /api/weather returns HTTP 400 for out-of-bounds latitude."""
        response = await self.client.get("/api/weather?latitude=105.0&longitude=77.35")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Latitude must be between -90.0 and 90.0 degrees", response.json()["detail"])

    # Test GET /api/weather with invalid longitude
    async def test_api_weather_invalid_longitude(self):
        """Verify GET /api/weather returns HTTP 400 for out-of-bounds longitude."""
        response = await self.client.get("/api/weather?latitude=16.20&longitude=-195.0")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Longitude must be between -180.0 and 180.0 degrees", response.json()["detail"])

    # Test GET /api/weather with missing parameters
    async def test_api_weather_missing_parameters(self):
        """Verify GET /api/weather returns HTTP 422 when required query parameters are missing."""
        response = await self.client.get("/api/weather")
        self.assertEqual(response.status_code, 422)

    # Test GET /api/weather with timeout
    async def test_api_weather_timeout(self):
        """Verify GET /api/weather returns HTTP 504 on upstream timeout."""
        with patch(
            "app.api.routes.weather.weather_service.get_current_weather",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = WeatherTimeoutError("Upstream timeout")

            response = await self.client.get("/api/weather?latitude=16.20&longitude=77.35")
            self.assertEqual(response.status_code, 504)
            self.assertIn("timed out", response.json()["detail"])

    # Test GET /api/weather with upstream rate limit
    async def test_api_weather_rate_limiting(self):
        """Verify GET /api/weather returns HTTP 429 when upstream rate limit is hit."""
        with patch(
            "app.api.routes.weather.weather_service.get_current_weather",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = WeatherRateLimitError("Rate limit exceeded")

            response = await self.client.get("/api/weather?latitude=16.20&longitude=77.35")
            self.assertEqual(response.status_code, 429)
            self.assertIn("rate limit exceeded", response.json()["detail"])

    # Test GET /api/weather with upstream HTTP 500 error
    async def test_api_weather_upstream_error(self):
        """Verify GET /api/weather returns HTTP 502 when upstream provider fails."""
        with patch(
            "app.api.routes.weather.weather_service.get_current_weather",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = WeatherProviderError("Weather provider error")

            response = await self.client.get("/api/weather?latitude=16.20&longitude=77.35")
            self.assertEqual(response.status_code, 502)
            self.assertIn("invalid or error response", response.json()["detail"])

    # Test GET /api/weather with network disconnect
    async def test_api_weather_network_failure(self):
        """Verify GET /api/weather returns HTTP 503 when network connection fails."""
        with patch(
            "app.api.routes.weather.weather_service.get_current_weather",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = WeatherConnectionError("Connection refused")

            response = await self.client.get("/api/weather?latitude=16.20&longitude=77.35")
            self.assertEqual(response.status_code, 503)
            self.assertIn("temporarily unavailable", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
