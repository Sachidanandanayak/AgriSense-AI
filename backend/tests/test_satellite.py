"""Comprehensive unit and API tests for AgriSense AI satellite data integration (Phase 5).

All unit tests are fully isolated and mock Earth Engine responses to ensure
deterministic execution without external network or Google Earth Engine credentials.
"""

from __future__ import annotations
import math
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import httpx
from pydantic import ValidationError

from app.main import app
from app.schemas.satellite import SatelliteResponse, IndexStatistics
from app.services.satellite_service import (
    SatelliteService,
    compute_ndvi,
    compute_ndwi,
    compute_ndmi,
    validate_coordinates,
    validate_date_range,
    validate_parameters,
    InvalidCoordinatesError,
    InvalidDateRangeError,
    InvalidParameterError,
    EarthEngineAuthError,
    EarthEngineInitError,
    NoObservationsFoundError,
    EarthEngineExecutionError,
)


# ===========================================================================
# 1. Deterministic Spectral Index Calculation Tests
# ===========================================================================


class TestSpectralIndexCalculations(unittest.TestCase):
    """Deterministic mathematical tests for NDVI, NDWI, and NDMI formulas."""

    def test_ndvi_standard_calculation(self):
        """10. Verify correct NDVI calculation: (B8 - B4) / (B8 + B4)."""
        # Vigorous healthy canopy: High NIR (0.8), Low Red (0.2)
        # NDVI = (0.8 - 0.2) / (0.8 + 0.2) = 0.6 / 1.0 = 0.6
        val = compute_ndvi(nir=0.8, red=0.2)
        self.assertAlmostEqual(val, 0.6, places=4)

    def test_ndvi_soil_or_senescent(self):
        """Verify NDVI for bare soil or non-vegetated surface."""
        # Bare soil: Moderate NIR (0.25), Moderate Red (0.20)
        # NDVI = (0.25 - 0.20) / (0.25 + 0.20) = 0.05 / 0.45 = 0.1111
        val = compute_ndvi(nir=0.25, red=0.20)
        self.assertAlmostEqual(val, 0.1111, places=3)

    def test_ndvi_zero_denominator_safe(self):
        """Verify NDVI safely returns 0.0 on zero denominator without NaN or inf."""
        val = compute_ndvi(nir=0.0, red=0.0)
        self.assertEqual(val, 0.0)
        self.assertFalse(math.isnan(val))
        self.assertFalse(math.isinf(val))

    def test_ndvi_near_zero_denominator_safe(self):
        """Verify NDVI safely returns 0.0 on near-zero denominator."""
        val = compute_ndvi(nir=1e-8, red=-1e-8)
        self.assertEqual(val, 0.0)

    def test_ndvi_clamping(self):
        """Verify NDVI output is strictly bounded to [-1.0, 1.0]."""
        val_high = compute_ndvi(nir=2.0, red=-0.5)
        self.assertLessEqual(val_high, 1.0)
        val_low = compute_ndvi(nir=-0.5, red=2.0)
        self.assertGreaterEqual(val_low, -1.0)

    def test_ndwi_mcfeeters_standard_water(self):
        """11. Verify correct NDWI calculation (McFeeters 1996): (B3 - B8) / (B3 + B8)."""
        # Open water body: High Green (0.3), Low NIR (0.05)
        # NDWI = (0.3 - 0.05) / (0.3 + 0.05) = 0.25 / 0.35 = 0.7143 (positive -> water)
        val = compute_ndwi(green=0.3, nir=0.05)
        self.assertAlmostEqual(val, 0.7143, places=3)
        self.assertGreater(val, 0.0)

    def test_ndwi_mcfeeters_terrestrial_vegetation(self):
        """Verify NDWI is negative over terrestrial vegetation canopy."""
        # Vegetation: Low Green (0.10), High NIR (0.60)
        # NDWI = (0.10 - 0.60) / (0.10 + 0.60) = -0.50 / 0.70 = -0.7143
        val = compute_ndwi(green=0.10, nir=0.60)
        self.assertAlmostEqual(val, -0.7143, places=3)
        self.assertLess(val, 0.0)

    def test_ndwi_zero_denominator_safe(self):
        """Verify NDWI safely handles zero denominator."""
        val = compute_ndwi(green=0.0, nir=0.0)
        self.assertEqual(val, 0.0)
        self.assertFalse(math.isnan(val))
        self.assertFalse(math.isinf(val))

    def test_ndmi_gao_standard_moisture(self):
        """12. Verify correct NDMI calculation (Gao 1996): (B8 - B11) / (B8 + B11)."""
        # Well-hydrated canopy: High NIR (0.6), Lower SWIR (0.2)
        # NDMI = (0.6 - 0.2) / (0.6 + 0.2) = 0.4 / 0.8 = 0.5
        val = compute_ndmi(nir=0.6, swir=0.2)
        self.assertAlmostEqual(val, 0.5, places=4)
        self.assertGreater(val, 0.0)

    def test_ndmi_gao_water_stress(self):
        """Verify NDMI yields low/negative values under severe moisture deficit."""
        # Water-stressed / dry canopy: Lower NIR (0.25), Higher SWIR (0.35)
        # NDMI = (0.25 - 0.35) / (0.25 + 0.35) = -0.10 / 0.60 = -0.1667
        val = compute_ndmi(nir=0.25, swir=0.35)
        self.assertAlmostEqual(val, -0.1667, places=3)

    def test_ndmi_zero_denominator_safe(self):
        """Verify NDMI safely handles zero denominator."""
        val = compute_ndmi(nir=0.0, swir=0.0)
        self.assertEqual(val, 0.0)
        self.assertFalse(math.isnan(val))
        self.assertFalse(math.isinf(val))


# ===========================================================================
# 2. Coordinate, Date Range & Parameter Validation Tests
# ===========================================================================


class TestInputValidationHelpers(unittest.TestCase):
    """Validation helper unit tests for coordinates, dates, and query parameters."""

    def test_01_valid_coordinates(self):
        """1. Verify valid coordinates pass without error."""
        try:
            validate_coordinates(16.20, 77.35)
            validate_coordinates(0.0, 0.0)
            validate_coordinates(-90.0, -180.0)
            validate_coordinates(90.0, 180.0)
        except InvalidCoordinatesError:
            self.fail("validate_coordinates raised InvalidCoordinatesError unexpectedly")

    def test_02_invalid_latitude(self):
        """2. Verify out-of-bounds latitude raises InvalidCoordinatesError."""
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(90.001, 77.35)
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(-90.1, 77.35)
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates("invalid_lat", 77.35)

    def test_03_invalid_longitude(self):
        """3. Verify out-of-bounds longitude raises InvalidCoordinatesError."""
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(16.20, 180.001)
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(16.20, -180.1)
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(16.20, "invalid_lon")

    def test_04_valid_date_range(self):
        """Verify valid date ranges are parsed correctly."""
        d_start, d_end = validate_date_range("2026-09-01", "2026-09-25")
        self.assertEqual(str(d_start), "2026-09-01")
        self.assertEqual(str(d_end), "2026-09-25")
        self.assertLessEqual(d_start, d_end)

        # Equal start and end dates are valid (single-day query)
        d_s, d_e = validate_date_range("2026-09-15", "2026-09-15")
        self.assertEqual(d_s, d_e)

    def test_04_invalid_date_range_ordering(self):
        """4. Verify start_date > end_date raises InvalidDateRangeError."""
        with self.assertRaises(InvalidDateRangeError) as ctx:
            validate_date_range("2026-09-25", "2026-09-01")
        self.assertIn("must be less than or equal to", str(ctx.exception))

    def test_04_malformed_dates(self):
        """Verify invalid date strings raise InvalidDateRangeError."""
        with self.assertRaises(InvalidDateRangeError):
            validate_date_range("2026/09/01", "2026-09-25")
        with self.assertRaises(InvalidDateRangeError):
            validate_date_range("2026-09-01", "not-a-date")
        with self.assertRaises(InvalidDateRangeError):
            validate_date_range("2026-02-31", "2026-03-05")

    def test_05_radius_validation(self):
        """5. Verify radius parameter bounds enforcement."""
        # Valid radii
        validate_parameters(radius_m=500.0, cloud_probability_threshold=65.0)
        validate_parameters(radius_m=10.0, cloud_probability_threshold=65.0)
        validate_parameters(radius_m=50000.0, cloud_probability_threshold=65.0)

        # Invalid radii
        with self.assertRaises(InvalidParameterError):
            validate_parameters(radius_m=0.0, cloud_probability_threshold=65.0)
        with self.assertRaises(InvalidParameterError):
            validate_parameters(radius_m=-50.0, cloud_probability_threshold=65.0)
        with self.assertRaises(InvalidParameterError):
            validate_parameters(radius_m=50000.1, cloud_probability_threshold=65.0)

    def test_06_cloud_threshold_validation(self):
        """6. Verify cloud probability threshold bounds enforcement."""
        # Valid thresholds
        validate_parameters(radius_m=500.0, cloud_probability_threshold=0.0)
        validate_parameters(radius_m=500.0, cloud_probability_threshold=65.0)
        validate_parameters(radius_m=500.0, cloud_probability_threshold=100.0)

        # Invalid thresholds
        with self.assertRaises(InvalidParameterError):
            validate_parameters(radius_m=500.0, cloud_probability_threshold=-0.1)
        with self.assertRaises(InvalidParameterError):
            validate_parameters(radius_m=500.0, cloud_probability_threshold=100.1)


# ===========================================================================
# 3. Pydantic Schema Validation Tests
# ===========================================================================


class TestSatelliteSchemaValidation(unittest.TestCase):
    """Pydantic schema validation tests for SatelliteResponse and IndexStatistics."""

    def test_valid_satellite_response(self):
        """Verify schema accepts authentic example payload."""
        data = {
            "latitude": 16.20,
            "longitude": 77.35,
            "radius_m": 500,
            "start_date": "2026-09-01",
            "end_date": "2026-09-25",
            "usable_observations": 3,
            "cloud_probability_threshold": 65,
            "ndvi_median": 0.54,
            "ndwi_median": 0.18,
            "ndmi_median": 0.31,
            "data_source": "Sentinel-2",
        }
        res = SatelliteResponse(**data)
        self.assertEqual(res.latitude, 16.20)
        self.assertEqual(res.longitude, 77.35)
        self.assertEqual(res.usable_observations, 3)
        self.assertEqual(res.ndvi_median, 0.54)
        self.assertEqual(res.ndwi_median, 0.18)
        self.assertEqual(res.ndmi_median, 0.31)
        self.assertIn("does not represent an exact farm boundary", res.disclaimer)

    def test_to_feature_dict(self):
        """Verify export to multi-source feature vector dictionary."""
        res = SatelliteResponse(
            latitude=16.20,
            longitude=77.35,
            radius_m=500,
            start_date="2026-09-01",
            end_date="2026-09-25",
            usable_observations=3,
            cloud_probability_threshold=65,
            ndvi_median=0.54,
            ndwi_median=-0.18,
            ndmi_median=0.31,
        )
        features = res.to_feature_dict()
        self.assertEqual(features["satellite_ndvi_median"], 0.54)
        self.assertEqual(features["satellite_ndwi_median"], -0.18)
        self.assertEqual(features["satellite_ndmi_median"], 0.31)

    def test_index_out_of_bounds_rejected(self):
        """Verify indices outside [-1.0, 1.0] are rejected by Pydantic."""
        with self.assertRaises(ValidationError):
            SatelliteResponse(
                latitude=16.20,
                longitude=77.35,
                radius_m=500,
                start_date="2026-09-01",
                end_date="2026-09-25",
                usable_observations=1,
                cloud_probability_threshold=65,
                ndvi_median=1.05,  # Exceeds max 1.0
                ndwi_median=0.18,
                ndmi_median=0.31,
            )

    def test_invalid_date_ordering_in_schema(self):
        """Verify schema rejects start_date > end_date."""
        with self.assertRaises(ValidationError):
            SatelliteResponse(
                latitude=16.20,
                longitude=77.35,
                radius_m=500,
                start_date="2026-09-25",
                end_date="2026-09-01",
                usable_observations=1,
                cloud_probability_threshold=65,
                ndvi_median=0.50,
                ndwi_median=0.10,
                ndmi_median=0.20,
            )


# ===========================================================================
# 4. Service Unit Tests (Mocking Earth Engine Pipeline)
# ===========================================================================


class TestSatelliteServiceMocked(unittest.IsolatedAsyncioTestCase):
    """Unit tests for SatelliteService business logic with mocked Earth Engine."""

    def setUp(self):
        self.service = SatelliteService(project_id="test-ee-project")

    async def test_07_successful_normalized_response(self):
        """7. Verify successful normalized response when Earth Engine returns valid data."""
        mock_pipeline_output = {
            "usable_observations": 3,
            "stats": {
                "ndvi_median": 0.5412,
                "ndvi_mean": 0.5280,
                "ndvi_min": 0.3100,
                "ndvi_max": 0.7200,
                "ndvi_stdDev": 0.0850,
                "ndwi_median": 0.1824,
                "ndwi_mean": 0.1750,
                "ndwi_min": -0.2100,
                "ndwi_max": 0.4500,
                "ndwi_stdDev": 0.0910,
                "ndmi_median": 0.3105,
                "ndmi_mean": 0.3010,
                "ndmi_min": 0.1200,
                "ndmi_max": 0.4800,
                "ndmi_stdDev": 0.0620,
            },
        }

        with patch.object(
            self.service,
            "_execute_earth_engine_pipeline",
            return_value=mock_pipeline_output,
        ):
            response = await self.service.get_satellite_data(
                latitude=16.20,
                longitude=77.35,
                start_date="2026-09-01",
                end_date="2026-09-25",
                radius_m=500.0,
                cloud_probability_threshold=65.0,
            )

            self.assertIsInstance(response, SatelliteResponse)
            self.assertEqual(response.latitude, 16.2)
            self.assertEqual(response.longitude, 77.35)
            self.assertEqual(response.usable_observations, 3)
            self.assertEqual(response.cloud_probability_threshold, 65.0)
            self.assertEqual(response.ndvi_median, 0.5412)
            self.assertEqual(response.ndwi_median, 0.1824)
            self.assertEqual(response.ndmi_median, 0.3105)
            self.assertEqual(response.data_source, "Sentinel-2")
            self.assertIsNotNone(response.statistics)
            self.assertEqual(response.statistics["ndvi"].median, 0.5412)

    async def test_08_missing_satellite_data(self):
        """8. Verify NoObservationsFoundError is raised when no usable imagery exists."""
        with patch.object(
            self.service,
            "_execute_earth_engine_pipeline",
            side_effect=NoObservationsFoundError(
                "No suitable cloud-free Sentinel-2 observation was found for the requested location and date range."
            ),
        ):
            with self.assertRaises(NoObservationsFoundError) as ctx:
                await self.service.get_satellite_data(
                    latitude=16.20,
                    longitude=77.35,
                    start_date="2026-09-01",
                    end_date="2026-09-25",
                )
            self.assertIn("No suitable cloud-free Sentinel-2 observation", str(ctx.exception))

    async def test_09_earth_engine_auth_failure(self):
        """9. Verify EarthEngineAuthError is raised when auth credentials fail."""
        with patch.object(
            self.service,
            "_execute_earth_engine_pipeline",
            side_effect=EarthEngineAuthError("Authentication failed"),
        ):
            with self.assertRaises(EarthEngineAuthError):
                await self.service.get_satellite_data(
                    latitude=16.20,
                    longitude=77.35,
                    start_date="2026-09-01",
                    end_date="2026-09-25",
                )

    async def test_09_earth_engine_execution_timeout(self):
        """Verify EarthEngineExecutionError is raised on timeout."""
        with patch.object(
            self.service,
            "_execute_earth_engine_pipeline",
            side_effect=EarthEngineExecutionError("Satellite service timed out"),
        ):
            with self.assertRaises(EarthEngineExecutionError):
                await self.service.get_satellite_data(
                    latitude=16.20,
                    longitude=77.35,
                    start_date="2026-09-01",
                    end_date="2026-09-25",
                )


# ===========================================================================
# 5. FastAPI HTTP Route Integration Tests (Mocked Service)
# ===========================================================================


class TestSatelliteApiEndpoints(unittest.IsolatedAsyncioTestCase):
    """Integration and HTTP route level tests for GET /api/satellite."""

    async def asyncSetUp(self):
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(
            transport=self.transport, base_url="http://testserver"
        )

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_api_satellite_success(self):
        """Verify GET /api/satellite returns HTTP 200 with normalized response."""
        mock_response = SatelliteResponse(
            latitude=16.20,
            longitude=77.35,
            radius_m=500.0,
            start_date="2026-09-01",
            end_date="2026-09-25",
            usable_observations=3,
            cloud_probability_threshold=65.0,
            ndvi_median=0.54,
            ndwi_median=0.18,
            ndmi_median=0.31,
            data_source="Sentinel-2",
        )

        with patch(
            "app.api.routes.satellite.satellite_service.get_satellite_data",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.return_value = mock_response

            response = await self.client.get(
                "/api/satellite?latitude=16.20&longitude=77.35&start_date=2026-09-01&end_date=2026-09-25"
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["latitude"], 16.20)
            self.assertEqual(data["longitude"], 77.35)
            self.assertEqual(data["radius_m"], 500.0)
            self.assertEqual(data["start_date"], "2026-09-01")
            self.assertEqual(data["end_date"], "2026-09-25")
            self.assertEqual(data["usable_observations"], 3)
            self.assertEqual(data["ndvi_median"], 0.54)
            self.assertEqual(data["ndwi_median"], 0.18)
            self.assertEqual(data["ndmi_median"], 0.31)
            self.assertEqual(data["data_source"], "Sentinel-2")
            self.assertIn("does not represent an exact farm boundary", data["disclaimer"])

    async def test_api_satellite_invalid_coordinates(self):
        """Verify GET /api/satellite returns HTTP 400 for out-of-bounds coordinates."""
        # Latitude out of bounds
        res_lat = await self.client.get(
            "/api/satellite?latitude=95.0&longitude=77.35&start_date=2026-09-01&end_date=2026-09-25"
        )
        self.assertEqual(res_lat.status_code, 400)
        self.assertIn("Latitude must be between -90.0 and 90.0", res_lat.json()["detail"])

        # Longitude out of bounds
        res_lon = await self.client.get(
            "/api/satellite?latitude=16.20&longitude=195.0&start_date=2026-09-01&end_date=2026-09-25"
        )
        self.assertEqual(res_lon.status_code, 400)
        self.assertIn("Longitude must be between -180.0 and 180.0", res_lon.json()["detail"])

    async def test_api_satellite_invalid_date_ordering(self):
        """Verify GET /api/satellite returns HTTP 400 when start_date > end_date."""
        response = await self.client.get(
            "/api/satellite?latitude=16.20&longitude=77.35&start_date=2026-09-25&end_date=2026-09-01"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("must be less than or equal to", response.json()["detail"])

    async def test_api_satellite_invalid_date_format(self):
        """Verify GET /api/satellite returns HTTP 400 for malformed dates."""
        response = await self.client.get(
            "/api/satellite?latitude=16.20&longitude=77.35&start_date=2026/09/01&end_date=2026-09-25"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid start_date", response.json()["detail"])

    async def test_api_satellite_invalid_radius(self):
        """Verify GET /api/satellite returns HTTP 400 for invalid radius."""
        response = await self.client.get(
            "/api/satellite?latitude=16.20&longitude=77.35&start_date=2026-09-01&end_date=2026-09-25&radius_m=-100"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("radius_m", response.json()["detail"])

    async def test_api_satellite_invalid_cloud_threshold(self):
        """Verify GET /api/satellite returns HTTP 400 for invalid cloud threshold."""
        response = await self.client.get(
            "/api/satellite?latitude=16.20&longitude=77.35&start_date=2026-09-01&end_date=2026-09-25&cloud_probability_threshold=150"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("cloud_probability_threshold", response.json()["detail"])

    async def test_api_satellite_no_observations_found(self):
        """Verify GET /api/satellite returns HTTP 404 when no cloud-free observation exists."""
        with patch(
            "app.api.routes.satellite.satellite_service.get_satellite_data",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = NoObservationsFoundError(
                "No suitable cloud-free Sentinel-2 observation was found for the requested location and date range."
            )

            response = await self.client.get(
                "/api/satellite?latitude=16.20&longitude=77.35&start_date=2026-09-01&end_date=2026-09-25"
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.json()["detail"],
                "No suitable cloud-free Sentinel-2 observation was found for the requested location and date range.",
            )

    async def test_api_satellite_auth_failure(self):
        """Verify GET /api/satellite returns HTTP 503 on unconfigured Earth Engine."""
        with patch(
            "app.api.routes.satellite.satellite_service.get_satellite_data",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = EarthEngineAuthError("Missing Earth Engine project")

            response = await self.client.get(
                "/api/satellite?latitude=16.20&longitude=77.35&start_date=2026-09-01&end_date=2026-09-25"
            )
            self.assertEqual(response.status_code, 503)
            self.assertIn("Earth Engine is not authenticated", response.json()["detail"])

    async def test_api_satellite_upstream_timeout(self):
        """Verify GET /api/satellite returns HTTP 504 on timeout."""
        with patch(
            "app.api.routes.satellite.satellite_service.get_satellite_data",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = EarthEngineExecutionError(
                "Satellite service timed out while querying Earth Engine."
            )

            response = await self.client.get(
                "/api/satellite?latitude=16.20&longitude=77.35&start_date=2026-09-01&end_date=2026-09-25"
            )
            self.assertEqual(response.status_code, 504)
            self.assertIn("timed out", response.json()["detail"])

    async def test_api_satellite_upstream_error(self):
        """Verify GET /api/satellite returns HTTP 502 on calculation/reduction failure."""
        with patch(
            "app.api.routes.satellite.satellite_service.get_satellite_data",
            new_callable=AsyncMock,
        ) as mock_svc:
            mock_svc.side_effect = EarthEngineExecutionError("Earth Engine internal error")

            response = await self.client.get(
                "/api/satellite?latitude=16.20&longitude=77.35&start_date=2026-09-01&end_date=2026-09-25"
            )
            self.assertEqual(response.status_code, 502)
            self.assertIn("Earth Engine returned an error", response.json()["detail"])


# ===========================================================================
# 6. Optional Live Earth Engine Integration Test (Skipped in standard CI)
# ===========================================================================


class TestEarthEngineLiveIntegration(unittest.IsolatedAsyncioTestCase):
    """Optional live integration tests connecting directly to Google Earth Engine.

    These tests are SKIPPED by default to ensure the standard test suite does
    not require live internet access or configured Earth Engine credentials.
    To execute live tests:
        set EARTHENGINE_LIVE_TEST=1
        backend/.venv/Scripts/python -m unittest backend/tests/test_satellite.py
    """

    @unittest.skipUnless(
        os.getenv("EARTHENGINE_LIVE_TEST") == "1",
        "Live Earth Engine test skipped unless EARTHENGINE_LIVE_TEST=1 is set.",
    )
    async def test_live_sentinel2_query(self):
        """Optional live test querying Sentinel-2 over a known agricultural region."""
        service = SatelliteService()
        # Query Raichur, Karnataka, India
        response = await service.get_satellite_data(
            latitude=16.20,
            longitude=77.35,
            start_date="2024-01-01",
            end_date="2024-01-31",
            radius_m=500.0,
            cloud_probability_threshold=65.0,
        )
        self.assertIsInstance(response, SatelliteResponse)
        self.assertGreater(response.usable_observations, 0)
        self.assertGreaterEqual(response.ndvi_median, -1.0)
        self.assertLessEqual(response.ndvi_median, 1.0)


if __name__ == "__main__":
    unittest.main()
