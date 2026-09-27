"""Comprehensive unit and API tests for AgriSense AI soil data integration (Phase 6).

All unit tests are fully isolated and mock external SoilGrids responses to ensure
deterministic execution without external network or API availability dependencies.
"""

from __future__ import annotations
import os
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
from app.schemas.soil import SoilResponse, SoilProperties
from app.services.soil_provider import (
    SoilGridsProvider,
    SOILGRIDS_PROPERTIES,
    SUPPORTED_DEPTH_INTERVALS,
    SoilProviderError,
    SoilProviderTimeoutError,
    SoilProviderConnectionError,
    SoilProviderRateLimitError,
    SoilProviderUnavailableError,
    MalformedSoilResponseError,
    NoSoilDataError,
)
from app.services.soil_service import (
    SoilService,
    validate_coordinates,
    validate_depth,
    InvalidCoordinatesError,
    InvalidDepthError,
)

# Authentic sample payload matching SoilGrids v2.0 REST API response structure
SAMPLE_SOILGRIDS_RESPONSE = {
    "type": "Feature",
    "geometry": {
        "type": "Point",
        "coordinates": [78.96, 20.59],
    },
    "properties": {
        "layers": [
            {
                "name": "phh2o",
                "unit_measure": {
                    "d_factor": 10,
                    "mapped_units": "pH*10",
                    "target_units": "pH",
                },
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": 72},
                    }
                ],
            },
            {
                "name": "clay",
                "unit_measure": {
                    "d_factor": 10,
                    "mapped_units": "g/kg",
                    "target_units": "%",
                },
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": 421},
                    }
                ],
            },
            {
                "name": "sand",
                "unit_measure": {
                    "d_factor": 10,
                    "mapped_units": "g/kg",
                    "target_units": "%",
                },
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": 194},
                    }
                ],
            },
            {
                "name": "silt",
                "unit_measure": {
                    "d_factor": 10,
                    "mapped_units": "g/kg",
                    "target_units": "%",
                },
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": 385},
                    }
                ],
            },
            {
                "name": "soc",
                "unit_measure": {
                    "d_factor": 10,
                    "mapped_units": "dg/kg",
                    "target_units": "g/kg",
                },
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": 121},
                    }
                ],
            },
            {
                "name": "bdod",
                "unit_measure": {
                    "d_factor": 100,
                    "mapped_units": "cg/cm³",
                    "target_units": "kg/dm³",
                },
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": 163},
                    }
                ],
            },
            {
                "name": "cec",
                "unit_measure": {
                    "d_factor": 10,
                    "mapped_units": "mmol(c)/kg",
                    "target_units": "cmol(c)/kg",
                },
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": 426},
                    }
                ],
            },
            {
                "name": "nitrogen",
                "unit_measure": {
                    "d_factor": 100,
                    "mapped_units": "cg/kg",
                    "target_units": "g/kg",
                },
                "depths": [
                    {
                        "range": {"top_depth": 0, "bottom_depth": 5, "unit_depth": "cm"},
                        "label": "0-5cm",
                        "values": {"mean": 134},
                    }
                ],
            },
        ]
    },
}


# ===========================================================================
# 1. Coordinate and Depth Validation Tests
# ===========================================================================


class TestSoilInputValidation(unittest.TestCase):
    """Unit tests for geographic coordinate and depth interval validation."""

    def test_01_valid_coordinates(self):
        """1. Verify valid coordinates pass without raising exceptions."""
        try:
            validate_coordinates(20.59, 78.96)
            validate_coordinates(0.0, 0.0)
            validate_coordinates(16.20, 77.35)
        except InvalidCoordinatesError:
            self.fail("validate_coordinates raised InvalidCoordinatesError unexpectedly.")

    def test_02_invalid_latitude(self):
        """2. Verify out-of-bounds latitude raises InvalidCoordinatesError."""
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(90.1, 78.96)
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(-95.0, 78.96)
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates("invalid_lat", 78.96)

    def test_03_invalid_longitude(self):
        """3. Verify out-of-bounds longitude raises InvalidCoordinatesError."""
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(20.59, 180.1)
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(20.59, -181.0)
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(20.59, "invalid_lon")

    def test_04_boundary_latitude(self):
        """4. Verify boundary latitudes (-90.0 and 90.0) are valid."""
        try:
            validate_coordinates(90.0, 0.0)
            validate_coordinates(-90.0, 0.0)
        except InvalidCoordinatesError:
            self.fail("Boundary latitudes failed validation unexpectedly.")

    def test_05_boundary_longitude(self):
        """5. Verify boundary longitudes (-180.0 and 180.0) are valid."""
        try:
            validate_coordinates(0.0, 180.0)
            validate_coordinates(0.0, -180.0)
        except InvalidCoordinatesError:
            self.fail("Boundary longitudes failed validation unexpectedly.")

    def test_06_valid_default_depth(self):
        """6. Verify valid depth intervals pass validation."""
        self.assertEqual(validate_depth("0-5cm"), "0-5cm")
        self.assertEqual(validate_depth("5-15cm"), "5-15cm")
        self.assertEqual(validate_depth("15-30cm"), "15-30cm")
        self.assertEqual(validate_depth("30-60cm"), "30-60cm")
        self.assertEqual(validate_depth("60-100cm"), "60-100cm")
        self.assertEqual(validate_depth("100-200cm"), "100-200cm")

    def test_07_unsupported_depth(self):
        """7. Verify unsupported depth intervals raise InvalidDepthError."""
        with self.assertRaises(InvalidDepthError):
            validate_depth("0-100cm")
        with self.assertRaises(InvalidDepthError):
            validate_depth("topsoil")
        with self.assertRaises(InvalidDepthError):
            validate_depth("")


# ===========================================================================
# 2. Service Normalization and Unit Conversion Tests
# ===========================================================================


class TestSoilServiceNormalization(unittest.TestCase):
    """Unit tests for SoilService normalization and conversion factors."""

    def setUp(self):
        self.service = SoilService()

    def test_08_successful_mocked_provider_response(self):
        """8. Verify successful parsing of authentic SoilGrids payload."""
        response = self.service.normalize_soil_data(
            raw_payload=SAMPLE_SOILGRIDS_RESPONSE,
            latitude=20.59,
            longitude=78.96,
            depth_interval="0-5cm",
        )
        self.assertIsInstance(response, SoilResponse)
        self.assertEqual(response.latitude, 20.59)
        self.assertEqual(response.longitude, 78.96)
        self.assertEqual(response.depth_interval, "0-5cm")
        self.assertEqual(response.data_source, "ISRIC SoilGrids 2.0")
        self.assertEqual(response.resolution_m, 250)

    def test_09_unit_conversion(self):
        """9. Verify explicit unit conversions according to official SoilGrids documentation.

        - phh2o: 72 / 10 = 7.2 pH
        - clay: 421 / 10 = 42.1%
        - sand: 194 / 10 = 19.4%
        - silt: 385 / 10 = 38.5%
        - soc: 121 / 10 = 12.1 g/kg
        - bdod: 163 / 100 = 1.63 kg/dm³
        - cec: 426 / 10 = 42.6 cmol(c)/kg
        - nitrogen: 134 / 100 = 1.34 g/kg
        """
        response = self.service.normalize_soil_data(
            raw_payload=SAMPLE_SOILGRIDS_RESPONSE,
            latitude=20.59,
            longitude=78.96,
            depth_interval="0-5cm",
        )
        soil = response.soil
        self.assertEqual(soil.ph, 7.2)
        self.assertEqual(soil.clay_pct, 42.1)
        self.assertEqual(soil.sand_pct, 19.4)
        self.assertEqual(soil.silt_pct, 38.5)
        self.assertEqual(soil.organic_carbon_g_kg, 12.1)
        self.assertEqual(soil.bulk_density, 1.63)
        self.assertEqual(soil.cec, 42.6)
        self.assertEqual(soil.nitrogen_g_kg, 1.34)

    def test_10_missing_property(self):
        """10. Verify missing property layer defaults to None without failing."""
        # Create payload missing 'nitrogen' layer
        layers_without_nitrogen = [
            l for l in SAMPLE_SOILGRIDS_RESPONSE["properties"]["layers"]
            if l["name"] != "nitrogen"
        ]
        partial_payload = {
            "type": "Feature",
            "properties": {"layers": layers_without_nitrogen},
        }
        response = self.service.normalize_soil_data(
            raw_payload=partial_payload,
            latitude=20.59,
            longitude=78.96,
            depth_interval="0-5cm",
        )
        self.assertIsNone(response.soil.nitrogen_g_kg)
        self.assertEqual(response.soil.ph, 7.2)


# ===========================================================================
# 3. Provider Layer HTTP & Error Handling Tests
# ===========================================================================


class TestSoilGridsProvider(unittest.IsolatedAsyncioTestCase):
    """Unit tests for SoilGridsProvider HTTP response handling and error mapping."""

    async def test_11_no_soil_data(self):
        """11. Verify NoSoilDataError is raised when all property layers return null (unmodeled mask)."""
        null_payload = {
            "type": "Feature",
            "properties": {
                "layers": [
                    {"name": "phh2o", "depths": [{"values": {"mean": None}}]},
                    {"name": "clay", "depths": [{"values": {"mean": None}}]},
                ]
            },
        }
        mock_response = httpx.Response(200, json=null_payload)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        provider = SoilGridsProvider(client=mock_client)
        with self.assertRaises(NoSoilDataError) as ctx:
            await provider.fetch_soil_data(16.20, 77.35)
        self.assertIn("No soil data available", str(ctx.exception))

    async def test_12_provider_timeout(self):
        """12. Verify SoilProviderTimeoutError is raised when upstream request times out."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timed out"))

        provider = SoilGridsProvider(client=mock_client)
        with self.assertRaises(SoilProviderTimeoutError):
            await provider.fetch_soil_data(20.59, 78.96)

    async def test_13_provider_http_failure_500(self):
        """13. Verify SoilProviderUnavailableError is raised on upstream 500 error."""
        mock_response = httpx.Response(500, text="Internal Server Error")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        provider = SoilGridsProvider(client=mock_client)
        with self.assertRaises(SoilProviderUnavailableError):
            await provider.fetch_soil_data(20.59, 78.96)

    async def test_provider_rate_limit_429(self):
        """Verify SoilProviderRateLimitError is raised on upstream 429."""
        mock_response = httpx.Response(429, text="Too Many Requests")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        provider = SoilGridsProvider(client=mock_client)
        with self.assertRaises(SoilProviderRateLimitError):
            await provider.fetch_soil_data(20.59, 78.96)

    async def test_provider_network_connection_error(self):
        """Verify SoilProviderConnectionError is raised on connection failure."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

        provider = SoilGridsProvider(client=mock_client)
        with self.assertRaises(SoilProviderConnectionError):
            await provider.fetch_soil_data(20.59, 78.96)

    async def test_14_malformed_response_json(self):
        """14. Verify MalformedSoilResponseError is raised on corrupted payload."""
        mock_response = httpx.Response(200, text="<not-json>")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        provider = SoilGridsProvider(client=mock_client)
        with self.assertRaises(MalformedSoilResponseError):
            await provider.fetch_soil_data(20.59, 78.96)


# ===========================================================================
# 4. Pydantic Schema Validation Tests
# ===========================================================================


class TestSoilSchemaValidation(unittest.TestCase):
    """15. Unit tests for Pydantic SoilResponse and SoilProperties schemas."""

    def test_15_pydantic_response_validation_valid(self):
        """15. Verify valid schema construction and feature dictionary export."""
        props = SoilProperties(
            ph=7.2,
            clay_pct=42.1,
            sand_pct=19.4,
            silt_pct=38.5,
            organic_carbon_g_kg=12.1,
            bulk_density=1.63,
            cec=42.6,
            nitrogen_g_kg=1.34,
        )
        res = SoilResponse(
            latitude=20.59,
            longitude=78.96,
            depth_interval="0-5cm",
            soil=props,
        )
        self.assertEqual(res.latitude, 20.59)
        self.assertEqual(res.soil.ph, 7.2)

        feat_dict = res.to_feature_dict()
        self.assertEqual(feat_dict["soil_ph"], 7.2)
        self.assertEqual(feat_dict["soil_clay_pct"], 42.1)
        self.assertEqual(feat_dict["soil_nitrogen_g_kg"], 1.34)

    def test_pydantic_rejects_out_of_bounds_ph(self):
        """Verify schema rejects pH outside physical range [0.0, 14.0]."""
        with self.assertRaises(ValidationError):
            SoilProperties(ph=15.0)

    def test_pydantic_rejects_negative_percentage(self):
        """Verify schema rejects negative clay percentage."""
        with self.assertRaises(ValidationError):
            SoilProperties(clay_pct=-5.0)


# ===========================================================================
# 5. FastAPI HTTP Route Integration Tests
# ===========================================================================


class TestSoilApiEndpoints(unittest.IsolatedAsyncioTestCase):
    """Integration and HTTP route level tests for GET /api/soil."""

    async def asyncSetUp(self):
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(
            transport=self.transport, base_url="http://testserver"
        )

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_api_soil_success(self):
        """Verify GET /api/soil returns HTTP 200 with normalized response."""
        mock_response = SoilResponse(
            latitude=20.59,
            longitude=78.96,
            depth_interval="0-5cm",
            soil=SoilProperties(
                ph=7.2,
                clay_pct=42.1,
                sand_pct=19.4,
                silt_pct=38.5,
                organic_carbon_g_kg=12.1,
                bulk_density=1.63,
                cec=42.6,
                nitrogen_g_kg=1.34,
            ),
        )

        with patch(
            "app.api.routes.soil.soil_service.get_soil_data",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = mock_response

            response = await self.client.get(
                "/api/soil?latitude=20.59&longitude=78.96&depth=0-5cm"
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["latitude"], 20.59)
            self.assertEqual(data["longitude"], 78.96)
            self.assertEqual(data["depth_interval"], "0-5cm")
            self.assertEqual(data["soil"]["ph"], 7.2)
            self.assertEqual(data["soil"]["clay_pct"], 42.1)
            self.assertEqual(data["data_source"], "ISRIC SoilGrids 2.0")

    async def test_api_soil_invalid_latitude(self):
        """Verify GET /api/soil returns HTTP 400 for out-of-bounds latitude."""
        response = await self.client.get("/api/soil?latitude=95.0&longitude=78.96")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Latitude must be between -90.0 and 90.0", response.json()["detail"])

    async def test_api_soil_invalid_longitude(self):
        """Verify GET /api/soil returns HTTP 400 for out-of-bounds longitude."""
        response = await self.client.get("/api/soil?latitude=20.59&longitude=195.0")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Longitude must be between -180.0 and 180.0", response.json()["detail"])

    async def test_api_soil_unsupported_depth(self):
        """Verify GET /api/soil returns HTTP 400 for unsupported depth interval."""
        response = await self.client.get(
            "/api/soil?latitude=20.59&longitude=78.96&depth=0-100cm"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported depth interval", response.json()["detail"])

    async def test_api_soil_no_soil_data_404(self):
        """Verify GET /api/soil returns HTTP 404 when coordinates fall outside modeled area."""
        with patch(
            "app.api.routes.soil.soil_service.get_soil_data",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = NoSoilDataError(
                "No soil data available from SoilGrids for the requested coordinates"
            )

            response = await self.client.get("/api/soil?latitude=16.20&longitude=77.35")
            self.assertEqual(response.status_code, 404)
            self.assertIn("No soil data available", response.json()["detail"])

    async def test_api_soil_timeout_504(self):
        """Verify GET /api/soil returns HTTP 504 on provider timeout."""
        with patch(
            "app.api.routes.soil.soil_service.get_soil_data",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = SoilProviderTimeoutError("SoilGrids timed out")

            response = await self.client.get("/api/soil?latitude=20.59&longitude=78.96")
            self.assertEqual(response.status_code, 504)
            self.assertIn("timed out", response.json()["detail"])

    async def test_api_soil_rate_limit_429(self):
        """Verify GET /api/soil returns HTTP 429 on rate limit exceeded."""
        with patch(
            "app.api.routes.soil.soil_service.get_soil_data",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = SoilProviderRateLimitError("Rate limit exceeded")

            response = await self.client.get("/api/soil?latitude=20.59&longitude=78.96")
            self.assertEqual(response.status_code, 429)
            self.assertIn("rate limit exceeded", response.json()["detail"])

    async def test_api_soil_unavailable_503(self):
        """Verify GET /api/soil returns HTTP 503 on upstream outage."""
        with patch(
            "app.api.routes.soil.soil_service.get_soil_data",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = SoilProviderUnavailableError("Server error 503")

            response = await self.client.get("/api/soil?latitude=20.59&longitude=78.96")
            self.assertEqual(response.status_code, 503)
            self.assertIn("temporarily unavailable", response.json()["detail"])

    async def test_api_soil_malformed_response_502(self):
        """Verify GET /api/soil returns HTTP 502 on malformed response."""
        with patch(
            "app.api.routes.soil.soil_service.get_soil_data",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = MalformedSoilResponseError("Corrupt payload")

            response = await self.client.get("/api/soil?latitude=20.59&longitude=78.96")
            self.assertEqual(response.status_code, 502)
            self.assertIn("unexpected or malformed response", response.json()["detail"])

    async def test_16_no_fake_fallback_values(self):
        """16. Verify that on provider failure, no synthetic or fake soil data is returned."""
        with patch(
            "app.api.routes.soil.soil_service.get_soil_data",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = SoilProviderError("Upstream failure")

            response = await self.client.get("/api/soil?latitude=20.59&longitude=78.96")
            self.assertEqual(response.status_code, 502)
            # Ensure no successful body or partial soil property dictionary is fabricated
            self.assertNotIn("soil", response.json())
            self.assertIn("detail", response.json())


# ===========================================================================
# 6. Optional Live SoilGrids Integration Test
# ===========================================================================


class TestSoilGridsLiveIntegration(unittest.IsolatedAsyncioTestCase):
    """Optional live integration tests connecting directly to SoilGrids REST API.

    These tests are SKIPPED by default to ensure the standard test suite does
    not require live internet access or depend on beta API availability.
    To execute:
        set SOILGRIDS_LIVE_TEST=1
        backend/.venv/Scripts/python -m unittest backend/tests/test_soil.py
    """

    @unittest.skipUnless(
        os.getenv("SOILGRIDS_LIVE_TEST") == "1",
        "Live SoilGrids test skipped unless SOILGRIDS_LIVE_TEST=1 is set.",
    )
    async def test_live_soilgrids_query(self):
        """Optional live test querying SoilGrids for known agricultural point."""
        service = SoilService()
        response = await service.get_soil_data(
            latitude=20.59,
            longitude=78.96,
            depth_interval="0-5cm",
        )
        self.assertIsInstance(response, SoilResponse)
        self.assertIsNotNone(response.soil.ph)
        self.assertGreaterEqual(response.soil.ph, 0.0)
        self.assertLessEqual(response.soil.ph, 14.0)


if __name__ == "__main__":
    unittest.main()
