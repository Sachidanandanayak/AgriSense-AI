"""Comprehensive test suite for Phase 8 Crop Suitability & Recommendation Engine."""

from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import httpx

from app.main import app
from app.schemas.satellite import IndexStatistics, SatelliteResponse
from app.schemas.soil import SoilProperties, SoilResponse
from app.schemas.weather import WeatherResponse
from app.services.feature_engineering.schemas import (
    AgriculturalFeatures,
    AlignmentMetadata,
    MultiSourceObservation,
)
from app.services.recommendation.exceptions import (
    IncompatibleFeatureSchemaError,
    InvalidCoordinatesError,
    InvalidDateError,
    MissingModelInputError,
    ModelPredictionError,
    ModelUnavailableError,
    RecommendationValidationError,
)
from app.services.recommendation.explanation import (
    generate_explanations,
    generate_limitations,
)
from app.services.recommendation.model_adapter import (
    CropModelAdapter,
    EXPECTED_MODEL_FEATURES,
    crop_model_adapter,
)
from app.services.recommendation.recommendation_service import (
    RecommendationService,
    recommendation_service,
)
from app.services.recommendation.schemas import (
    AgriculturalInput,
    CropRecommendationItem,
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
from app.services.weather_service import WeatherTimeoutError
from app.services.satellite_service import EarthEngineInitError
from app.services.soil_service import SoilProviderTimeoutError


class TestModelAdapter(unittest.TestCase):
    """Unit tests for CropModelAdapter and benchmark model compatibility boundary."""

    def setUp(self):
        self.adapter = CropModelAdapter()

    def test_01_model_loading_and_attributes(self):
        """1. Verify model loads safely, classes match 22 crops, and is_loaded is True."""
        self.adapter.load_model()
        self.assertTrue(self.adapter.is_loaded)
        self.assertEqual(len(self.adapter.classes), 22)
        self.assertEqual(len(self.adapter.feature_names), 11)

    def test_02_exact_model_feature_ordering(self):
        """2. Verify exact model feature ordering matches training contract."""
        expected = [
            "N",
            "P",
            "K",
            "temperature",
            "humidity",
            "ph",
            "rainfall",
            "N_P_ratio",
            "N_K_ratio",
            "P_K_ratio",
            "rain_temp_ratio",
        ]
        self.assertEqual(EXPECTED_MODEL_FEATURES, expected)
        self.assertEqual(self.adapter.feature_names, expected)

    def test_03_adapt_agricultural_inputs_computes_ratios(self):
        """3. Verify domain ratios are correctly calculated from raw agricultural inputs."""
        agri = AgriculturalInput(
            nitrogen=90.0,
            phosphorus=42.0,
            potassium=43.0,
            temperature=20.87,
            humidity=82.0,
            ph=6.5,
            rainfall=202.93,
        )
        adapted = self.adapter.adapt_agricultural_inputs(agri)

        # Check all 11 keys exist
        self.assertEqual(list(adapted.keys()), EXPECTED_MODEL_FEATURES)

        # Verify values
        self.assertEqual(adapted["N"], 90.0)
        self.assertEqual(adapted["P"], 42.0)
        self.assertEqual(adapted["K"], 43.0)
        self.assertAlmostEqual(adapted["N_P_ratio"], 90.0 / (42.0 + 1e-5), places=3)
        self.assertAlmostEqual(adapted["N_K_ratio"], 90.0 / (43.0 + 1e-5), places=3)
        self.assertAlmostEqual(adapted["P_K_ratio"], 42.0 / (43.0 + 1e-5), places=3)
        self.assertAlmostEqual(adapted["rain_temp_ratio"], 202.93 / (20.87 + 1e-5), places=3)

    def test_04_adapt_agricultural_inputs_rejects_missing_without_silent_imputation(self):
        """4. Verify missing inputs are rejected with MissingModelInputError (no silent imputation)."""
        incomplete = {
            "nitrogen": 80.0,
            "phosphorus": 40.0,
            # missing potassium
            "temperature": 25.0,
            "humidity": 60.0,
            "ph": 6.5,
            "rainfall": 100.0,
        }
        with self.assertRaises(MissingModelInputError) as ctx:
            self.adapter.adapt_agricultural_inputs(incomplete)
        self.assertIn("potassium", str(ctx.exception))
        self.assertIn("Silent imputation is strictly prohibited", str(ctx.exception))

    def test_05_incompatible_feature_schema_rejection(self):
        """5. Verify predict_top_k rejects incomplete feature schemas."""
        incomplete_features = {
            "N": 80.0,
            "P": 40.0,
            # Missing K and other columns
        }
        with self.assertRaises(IncompatibleFeatureSchemaError):
            self.adapter.predict_top_k(incomplete_features, k=3)

        # Extra columns or None values
        none_features = {f: 10.0 for f in EXPECTED_MODEL_FEATURES}
        none_features["temperature"] = None
        with self.assertRaises(MissingModelInputError):
            self.adapter.predict_top_k(none_features, k=3)

    def test_06_model_prediction_top_k_ordering(self):
        """6. Verify top-K predictions are returned with correct length, rank, and descending order."""
        features = {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.87,
            "humidity": 82.0,
            "ph": 6.5,
            "rainfall": 202.93,
            "N_P_ratio": 2.1428,
            "N_K_ratio": 2.0930,
            "P_K_ratio": 0.9767,
            "rain_temp_ratio": 9.7231,
        }
        recs = self.adapter.predict_top_k(features, k=3)
        self.assertEqual(len(recs), 3)

        # Check ranks
        self.assertEqual([r.rank for r in recs], [1, 2, 3])

        # Check descending probability
        self.assertGreaterEqual(recs[0].probability_estimate, recs[1].probability_estimate)
        self.assertGreaterEqual(recs[1].probability_estimate, recs[2].probability_estimate)

        # Check all crops are unique
        crops = [r.crop for r in recs]
        self.assertEqual(len(set(crops)), 3)

    def test_07_probability_estimate_output_naming(self):
        """7. Verify probability estimate output terminology (not suitability percentage)."""
        features = {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.87,
            "humidity": 82.0,
            "ph": 6.5,
            "rainfall": 202.93,
            "N_P_ratio": 2.1428,
            "N_K_ratio": 2.0930,
            "P_K_ratio": 0.9767,
            "rain_temp_ratio": 9.7231,
        }
        recs = self.adapter.predict_top_k(features, k=1)
        item = recs[0]

        # Verify fields
        self.assertTrue(hasattr(item, "probability_estimate"))
        self.assertTrue(hasattr(item, "confidence_percentage"))
        self.assertIsInstance(item.probability_estimate, float)
        self.assertTrue(0.0 <= item.probability_estimate <= 1.0)
        self.assertTrue(item.confidence_percentage.endswith("%"))

    def test_08_deterministic_prediction(self):
        """8. Verify identical inputs produce deterministic output across consecutive invocations."""
        features = {
            "N": 60.0,
            "P": 55.0,
            "K": 40.0,
            "temperature": 23.0,
            "humidity": 70.0,
            "ph": 6.2,
            "rainfall": 150.0,
            "N_P_ratio": 1.09,
            "N_K_ratio": 1.5,
            "P_K_ratio": 1.375,
            "rain_temp_ratio": 6.52,
        }
        run1 = self.adapter.predict_top_k(features, k=5)
        run2 = self.adapter.predict_top_k(features, k=5)

        for r1, r2 in zip(run1, run2):
            self.assertEqual(r1.crop, r2.crop)
            self.assertEqual(r1.rank, r2.rank)
            self.assertEqual(r1.probability_estimate, r2.probability_estimate)

    def test_09_model_unavailable_handling(self):
        """9. Verify ModelUnavailableError is raised if artifact is missing."""
        bogus_adapter = CropModelAdapter(model_path=Path("non_existent_model.joblib"))
        with self.assertRaises(ModelUnavailableError):
            bogus_adapter.load_model()

    def test_10_prediction_failure_handling(self):
        """10. Verify ModelPredictionError is raised if underlying model predict_proba fails."""
        mock_model = MagicMock()
        mock_model.predict_proba.side_effect = RuntimeError("Internal linear algebra error")
        adapter = CropModelAdapter()
        adapter._model = mock_model
        adapter._feature_names = EXPECTED_MODEL_FEATURES
        adapter._classes = ["cropA", "cropB"]

        features = {f: 1.0 for f in EXPECTED_MODEL_FEATURES}
        with self.assertRaises(ModelPredictionError):
            adapter.predict_top_k(features, k=2)

    def test_11_adapt_from_multisource_observation(self):
        """11. Verify adapting from Phase 7 MultiSourceObservation extracts 11 features."""
        meta = AlignmentMetadata(latitude=16.20, longitude=77.35)
        agri = AgriculturalFeatures(
            nitrogen=75.0,
            phosphorus=35.0,
            potassium=38.0,
            historical_temperature=27.0,
            historical_humidity=65.0,
            historical_ph=6.7,
            historical_rainfall=130.0,
        )
        obs = MultiSourceObservation(metadata=meta, agricultural=agri)

        adapted = self.adapter.adapt_from_multisource_observation(obs)
        self.assertEqual(list(adapted.keys()), EXPECTED_MODEL_FEATURES)
        self.assertEqual(adapted["N"], 75.0)
        self.assertEqual(adapted["P"], 35.0)
        self.assertEqual(adapted["K"], 38.0)
        self.assertEqual(adapted["temperature"], 27.0)


class TestRecommendationServiceAndOrchestration(unittest.IsolatedAsyncioTestCase):
    """Unit tests for RecommendationService end-to-end orchestration."""

    def setUp(self):
        self.service = RecommendationService()
        self.valid_agri = AgriculturalInput(
            nitrogen=90.0,
            phosphorus=42.0,
            potassium=43.0,
            temperature=20.87,
            humidity=82.0,
            ph=6.5,
            rainfall=202.93,
        )

    async def test_12_valid_recommendation_request(self):
        """12. Verify valid recommendation request produces structured RecommendationResponse."""
        request = RecommendationRequest(
            latitude=16.20,
            longitude=77.35,
            observation_date="2026-09-25",
            agricultural_inputs=self.valid_agri,
            top_k=3,
        )
        response = await self.service.generate_recommendation(request)

        self.assertIsInstance(response, RecommendationResponse)
        self.assertEqual(response.latitude, 16.20)
        self.assertEqual(response.longitude, 77.35)
        self.assertEqual(response.observation_date, "2026-09-25")
        self.assertEqual(len(response.recommendations), 3)

        # Check top recommendation is rice for these inputs
        self.assertEqual(response.recommendations[0].crop, "rice")
        self.assertEqual(response.recommendations[0].rank, 1)
        self.assertGreater(response.recommendations[0].probability_estimate, 0.5)

        # Check disclaimer
        self.assertEqual(response.disclaimer, MANDATORY_DISCLAIMER)

        # Check model input features recorded in response
        self.assertEqual(list(response.model_input_features.keys()), EXPECTED_MODEL_FEATURES)

    async def test_13_flat_agricultural_inputs_convenience(self):
        """13. Verify flat agricultural input parameters are automatically resolved."""
        request_dict = {
            "latitude": 16.20,
            "longitude": 77.35,
            "nitrogen": 90.0,
            "phosphorus": 42.0,
            "potassium": 43.0,
            "temperature": 20.87,
            "humidity": 82.0,
            "ph": 6.5,
            "rainfall": 202.93,
            "top_k": 3,
        }
        req = RecommendationRequest(**request_dict)
        self.assertIsNotNone(req.agricultural_inputs)
        self.assertEqual(req.agricultural_inputs.nitrogen, 90.0)

        response = await self.service.generate_recommendation(req)
        self.assertEqual(len(response.recommendations), 3)

    async def test_14_missing_weather_context_does_not_fabricate(self):
        """14. Verify missing weather context is reported honestly with no fabricated values."""
        request = RecommendationRequest(
            latitude=16.20,
            longitude=77.35,
            agricultural_inputs=self.valid_agri,
            fetch_live_weather=False,
        )
        response = await self.service.generate_recommendation(request)

        self.assertIsNone(response.environmental_context.weather)
        self.assertFalse(response.data_quality.weather_available)
        self.assertIn("weather", response.data_quality.missing_sources)

        # Check explanation notes that weather was unavailable
        exp_text = " ".join(response.explanation)
        self.assertIn("Weather data was unavailable", exp_text)

        # Check limitation includes missing weather
        lim_text = " ".join(response.limitations)
        self.assertIn("Missing Weather Context", lim_text)

    async def test_15_missing_satellite_context_does_not_fabricate(self):
        """15. Verify missing satellite context is reported honestly with no fabricated values."""
        request = RecommendationRequest(
            latitude=16.20,
            longitude=77.35,
            agricultural_inputs=self.valid_agri,
            fetch_live_satellite=False,
        )
        response = await self.service.generate_recommendation(request)

        self.assertIsNone(response.environmental_context.satellite)
        self.assertFalse(response.data_quality.satellite_available)
        self.assertIn("satellite", response.data_quality.missing_sources)

        exp_text = " ".join(response.explanation)
        self.assertIn("Satellite observations were unavailable", exp_text)

    async def test_16_missing_soil_context_does_not_fabricate(self):
        """16. Verify missing soil context is reported honestly with no fabricated values."""
        request = RecommendationRequest(
            latitude=16.20,
            longitude=77.35,
            agricultural_inputs=self.valid_agri,
            fetch_live_soil=False,
        )
        response = await self.service.generate_recommendation(request)

        self.assertIsNone(response.environmental_context.soil)
        self.assertFalse(response.data_quality.soil_available)
        self.assertIn("soil", response.data_quality.missing_sources)

        exp_text = " ".join(response.explanation)
        self.assertIn("Soil data was unavailable", exp_text)

    async def test_17_supplied_environmental_context_enrichment(self):
        """17. Verify pre-fetched environmental contexts are attached and reflected in data quality."""
        mock_weather = WeatherResponse(
            latitude=16.20,
            longitude=77.35,
            temperature_c=28.4,
            humidity_percent=64.0,
            rainfall_mm=0.0,
            wind_speed_mps=3.2,
            weather_timestamp="2026-09-25T12:00",
        )
        mock_satellite = SatelliteResponse(
            latitude=16.20,
            longitude=77.35,
            radius_m=500.0,
            start_date="2026-09-11",
            end_date="2026-09-25",
            usable_observations=3,
            cloud_probability_threshold=65.0,
            ndvi_median=0.55,
            ndwi_median=0.15,
            ndmi_median=0.28,
            data_source="Sentinel-2",
        )
        mock_soil = SoilResponse(
            latitude=16.20,
            longitude=77.35,
            depth_interval="0-5cm",
            soil=SoilProperties(
                ph=6.8,
                clay_pct=35.0,
                sand_pct=25.0,
                silt_pct=40.0,
                organic_carbon_g_kg=14.2,
            ),
            data_source="ISRIC SoilGrids 2.0",
        )

        request = RecommendationRequest(
            latitude=16.20,
            longitude=77.35,
            observation_date="2026-09-25",
            agricultural_inputs=self.valid_agri,
            weather_context=mock_weather,
            satellite_context=mock_satellite,
            soil_context=mock_soil,
        )

        response = await self.service.generate_recommendation(request)

        # Check contexts are attached
        self.assertIsNotNone(response.environmental_context.weather)
        self.assertEqual(response.environmental_context.weather.temperature_c, 28.4)
        self.assertIsNotNone(response.environmental_context.satellite)
        self.assertEqual(response.environmental_context.satellite.ndvi_median, 0.55)
        self.assertIsNotNone(response.environmental_context.soil)
        self.assertEqual(response.environmental_context.soil.soil.ph, 6.8)

        # Check data quality
        self.assertTrue(response.data_quality.weather_available)
        self.assertTrue(response.data_quality.satellite_available)
        self.assertTrue(response.data_quality.soil_available)
        self.assertEqual(len(response.data_quality.missing_sources), 0)

        # Check explanations cite the contextual values without asserting proof
        exp_text = " ".join(response.explanation)
        self.assertIn("28.4°C air temperature", exp_text)
        self.assertIn("median NDVI of 0.55", exp_text)
        self.assertIn("not direct proof of crop suitability", exp_text)
        self.assertIn("ISRIC SoilGrids 2.0 at 0-5cm", exp_text)

    async def test_18_provenance_and_limitations_integrity(self):
        """18. Verify provenance metadata and explicit limitations are properly generated."""
        request = RecommendationRequest(
            latitude=16.20,
            longitude=77.35,
            agricultural_inputs=self.valid_agri,
        )
        response = await self.service.generate_recommendation(request)

        dq = response.data_quality
        self.assertEqual(dq.model_version, "crop_recommendation_rf_v1")
        self.assertTrue(dq.model_available)

        # Check all limitation statements
        lims = response.limitations
        self.assertTrue(any("2,200-sample benchmark" in l for l in lims))
        self.assertTrue(any("NDVI" in l for l in lims))
        self.assertTrue(any("SoilGrids 2.0" in l for l in lims))
        self.assertTrue(any("Unmodelled Agronomic Risks" in l for l in lims))

    async def test_19_live_fetch_failure_degrades_gracefully(self):
        """19. Verify live fetch provider failures degrade gracefully with warnings."""
        mock_weather_svc = MagicMock()
        mock_weather_svc.get_current_weather = AsyncMock(
            side_effect=WeatherTimeoutError("Open-Meteo timeout")
        )

        mock_satellite_svc = MagicMock()
        mock_satellite_svc.get_satellite_indices = AsyncMock(
            side_effect=EarthEngineInitError("EE missing")
        )

        mock_soil_svc = MagicMock()
        mock_soil_svc.get_soil_data = AsyncMock(
            side_effect=SoilProviderTimeoutError("SoilGrids timeout")
        )

        service = RecommendationService(
            weather_svc=mock_weather_svc,
            satellite_svc=mock_satellite_svc,
            soil_svc=mock_soil_svc,
        )

        request = RecommendationRequest(
            latitude=16.20,
            longitude=77.35,
            agricultural_inputs=self.valid_agri,
            fetch_live_weather=True,
            fetch_live_satellite=True,
            fetch_live_soil=True,
        )

        response = await service.generate_recommendation(request)

        # Recommendation still succeeds
        self.assertEqual(len(response.recommendations), 3)

        # Providers marked unavailable
        self.assertFalse(response.data_quality.weather_available)
        self.assertFalse(response.data_quality.satellite_available)
        self.assertFalse(response.data_quality.soil_available)

        # Warnings recorded
        self.assertGreaterEqual(len(response.data_quality.warnings), 3)


class TestValidatorsAndErrorHandling(unittest.TestCase):
    """Unit tests for request validators and error conditions."""

    def test_20_invalid_latitude(self):
        """20. Verify latitude out of bounds raises InvalidCoordinatesError."""
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(-95.0, 77.0)
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(95.0, 77.0)
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates("invalid", 77.0)

    def test_21_invalid_longitude(self):
        """21. Verify longitude out of bounds raises InvalidCoordinatesError."""
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(16.0, -185.0)
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(16.0, 185.0)
        with self.assertRaises(InvalidCoordinatesError):
            validate_coordinates(16.0, None)

    def test_22_invalid_observation_date(self):
        """22. Verify invalid date string raises InvalidDateError."""
        with self.assertRaises(InvalidDateError):
            validate_observation_date("2026-13-45")
        with self.assertRaises(InvalidDateError):
            validate_observation_date("not-a-date")
        self.assertIsNone(validate_observation_date(None))
        self.assertEqual(validate_observation_date("2026-09-25"), "2026-09-25")
        self.assertEqual(validate_observation_date(date(2026, 9, 25)), "2026-09-25")

    def test_23_missing_agricultural_inputs_raises_error(self):
        """23. Verify missing agricultural inputs raises MissingModelInputError."""
        with self.assertRaises(MissingModelInputError):
            validate_agricultural_inputs(None)

    def test_24_invalid_top_k(self):
        """24. Verify top_k out of range raises RecommendationValidationError."""
        with self.assertRaises(RecommendationValidationError):
            validate_top_k(0)
        with self.assertRaises(RecommendationValidationError):
            validate_top_k(25)
        with self.assertRaises(RecommendationValidationError):
            validate_top_k("invalid")
        self.assertEqual(validate_top_k(5), 5)


class TestRecommendationApiEndpoint(unittest.IsolatedAsyncioTestCase):
    """Integration tests for POST /api/recommendations HTTP endpoint."""

    async def asyncSetUp(self):
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_25_api_recommendation_success_200(self):
        """25. Verify POST /api/recommendations returns 200 with valid payload."""
        payload = {
            "latitude": 16.20,
            "longitude": 77.35,
            "observation_date": "2026-09-25",
            "agricultural_inputs": {
                "nitrogen": 90.0,
                "phosphorus": 42.0,
                "potassium": 43.0,
                "temperature": 20.87,
                "humidity": 82.0,
                "ph": 6.5,
                "rainfall": 202.93,
            },
            "top_k": 3,
        }
        res = await self.client.post("/api/recommendations", json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(data["latitude"], 16.20)
        self.assertEqual(data["longitude"], 77.35)
        self.assertEqual(len(data["recommendations"]), 3)
        self.assertEqual(data["recommendations"][0]["crop"], "rice")
        self.assertIn("probability_estimate", data["recommendations"][0])
        self.assertIn("model_input_features", data)
        self.assertEqual(len(data["model_input_features"]), 11)
        self.assertIn("disclaimer", data)

    async def test_26_api_recommendation_flat_inputs_200(self):
        """26. Verify POST /api/recommendations succeeds with flat inputs."""
        payload = {
            "latitude": 16.20,
            "longitude": 77.35,
            "nitrogen": 90.0,
            "phosphorus": 42.0,
            "potassium": 43.0,
            "temperature": 20.87,
            "humidity": 82.0,
            "ph": 6.5,
            "rainfall": 202.93,
            "top_k": 3,
        }
        res = await self.client.post("/api/recommendations", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["recommendations"][0]["crop"], "rice")

    async def test_27_api_missing_required_model_inputs_returns_400(self):
        """27. Verify POST /api/recommendations returns 400 when model inputs are omitted."""
        payload = {
            "latitude": 16.20,
            "longitude": 77.35,
            # Missing agricultural inputs
        }
        res = await self.client.post("/api/recommendations", json=payload)
        self.assertEqual(res.status_code, 400)
        detail = res.json()["detail"]
        self.assertIn("Missing required agricultural inputs", detail)
        self.assertIn("Silent imputation is strictly prohibited", detail)

    async def test_28_api_invalid_coordinates_returns_400_or_422(self):
        """28. Verify POST /api/recommendations returns error on coordinate bounds violation."""
        payload = {
            "latitude": 99.0,  # invalid latitude > 90
            "longitude": 77.35,
            "nitrogen": 80.0,
            "phosphorus": 40.0,
            "potassium": 40.0,
            "temperature": 25.0,
            "humidity": 60.0,
            "ph": 6.5,
            "rainfall": 100.0,
        }
        res = await self.client.post("/api/recommendations", json=payload)
        self.assertIn(res.status_code, [400, 422])

    async def test_29_api_invalid_date_returns_400(self):
        """29. Verify POST /api/recommendations returns 400 on malformed date string."""
        payload = {
            "latitude": 16.20,
            "longitude": 77.35,
            "observation_date": "2026-99-99",
            "agricultural_inputs": {
                "nitrogen": 80.0,
                "phosphorus": 40.0,
                "potassium": 40.0,
                "temperature": 25.0,
                "humidity": 60.0,
                "ph": 6.5,
                "rainfall": 100.0,
            },
        }
        res = await self.client.post("/api/recommendations", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid date format", res.json()["detail"])

    async def test_30_api_model_unavailable_returns_503(self):
        """30. Verify POST /api/recommendations returns 503 if model is unavailable."""
        with patch.object(
            recommendation_service.model_adapter,
            "load_model",
            side_effect=ModelUnavailableError("Model artifact missing"),
        ):
            payload = {
                "latitude": 16.20,
                "longitude": 77.35,
                "agricultural_inputs": {
                    "nitrogen": 80.0,
                    "phosphorus": 40.0,
                    "potassium": 40.0,
                    "temperature": 25.0,
                    "humidity": 60.0,
                    "ph": 6.5,
                    "rainfall": 100.0,
                },
            }
            res = await self.client.post("/api/recommendations", json=payload)
            self.assertEqual(res.status_code, 503)
            self.assertIn("currently unavailable", res.json()["detail"])

    async def test_31_temporal_alignment_future_satellite_rejected(self):
        """31. Verify satellite window ending after observation_date is rejected (temporal leakage)."""
        mock_satellite = SatelliteResponse(
            latitude=16.20,
            longitude=77.35,
            radius_m=500.0,
            start_date="2026-09-01",
            end_date="2026-09-15",  # Future relative to 2026-09-10
            usable_observations=3,
            cloud_probability_threshold=65.0,
            ndvi_median=0.55,
            ndwi_median=0.15,
            ndmi_median=0.28,
            data_source="Sentinel-2",
        )
        request = RecommendationRequest(
            latitude=16.20,
            longitude=77.35,
            observation_date="2026-09-10",
            agricultural_inputs=AgriculturalInput(
                nitrogen=90.0,
                phosphorus=42.0,
                potassium=43.0,
                temperature=20.87,
                humidity=82.0,
                ph=6.5,
                rainfall=202.93,
            ),
            satellite_context=mock_satellite,
        )
        with self.assertRaises(RecommendationValidationError) as ctx:
            await recommendation_service.generate_recommendation(request)
        self.assertIn("future data leakage detected", str(ctx.exception).lower())

    async def test_32_temporal_alignment_future_weather_rejected(self):
        """32. Verify weather timestamp after observation_date is rejected (temporal leakage)."""
        mock_weather = WeatherResponse(
            latitude=16.20,
            longitude=77.35,
            temperature_c=28.4,
            humidity_percent=64.0,
            rainfall_mm=0.0,
            wind_speed_mps=3.2,
            weather_timestamp="2026-09-15T12:00",  # Future relative to 2026-09-10
        )
        request = RecommendationRequest(
            latitude=16.20,
            longitude=77.35,
            observation_date="2026-09-10",
            agricultural_inputs=AgriculturalInput(
                nitrogen=90.0,
                phosphorus=42.0,
                potassium=43.0,
                temperature=20.87,
                humidity=82.0,
                ph=6.5,
                rainfall=202.93,
            ),
            weather_context=mock_weather,
        )
        with self.assertRaises(RecommendationValidationError) as ctx:
            await recommendation_service.generate_recommendation(request)
        self.assertIn("is after target observation date", str(ctx.exception).lower())

    async def test_33_spatial_alignment_tolerance_enforced(self):
        """33. Verify coordinates differing by >0.005° are rejected by spatial alignment check."""
        # 16.21 vs 16.20 is diff of 0.010° > 0.005° tolerance (~550m)
        misaligned_weather = WeatherResponse(
            latitude=16.21,
            longitude=77.35,
            temperature_c=28.4,
            humidity_percent=64.0,
            rainfall_mm=0.0,
            wind_speed_mps=3.2,
            weather_timestamp="2026-09-10T12:00",
        )
        request = RecommendationRequest(
            latitude=16.20,
            longitude=77.35,
            observation_date="2026-09-10",
            agricultural_inputs=AgriculturalInput(
                nitrogen=90.0,
                phosphorus=42.0,
                potassium=43.0,
                temperature=20.87,
                humidity=82.0,
                ph=6.5,
                rainfall=202.93,
            ),
            weather_context=misaligned_weather,
        )
        with self.assertRaises(RecommendationValidationError) as ctx:
            await recommendation_service.generate_recommendation(request)
        self.assertIn("exceeding engineering tolerance", str(ctx.exception).lower())

    async def test_34_phase7_feature_builder_not_bypassed(self):
        """34. Verify Phase 7 MultiSourceFeatureBuilder is invoked when context is supplied."""
        mock_weather = WeatherResponse(
            latitude=16.20,
            longitude=77.35,
            temperature_c=28.4,
            humidity_percent=64.0,
            rainfall_mm=0.0,
            wind_speed_mps=3.2,
            weather_timestamp="2026-09-25T12:00",
        )
        request = RecommendationRequest(
            latitude=16.20,
            longitude=77.35,
            observation_date="2026-09-25",
            agricultural_inputs=AgriculturalInput(
                nitrogen=90.0,
                phosphorus=42.0,
                potassium=43.0,
                temperature=20.87,
                humidity=82.0,
                ph=6.5,
                rainfall=202.93,
            ),
            weather_context=mock_weather,
        )

        with patch.object(
            recommendation_service.feature_builder,
            "build_unified_observation",
            wraps=recommendation_service.feature_builder.build_unified_observation,
        ) as spy_builder:
            response = await recommendation_service.generate_recommendation(request)
            spy_builder.assert_called_once()
            self.assertEqual(response.latitude, 16.20)

    def test_35_benchmark_model_receives_only_11_features(self):
        """35. Verify the model predict_proba input receives exactly and only the 11 expected features."""
        adapter = CropModelAdapter()
        adapter.load_model()

        captured_input = []
        original_predict_proba = adapter._model.predict_proba

        def inspect_predict_proba(df_input):
            captured_input.append(df_input)
            return original_predict_proba(df_input)

        adapter._model.predict_proba = inspect_predict_proba

        features = {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.87,
            "humidity": 82.0,
            "ph": 6.5,
            "rainfall": 202.93,
            "N_P_ratio": 2.1428,
            "N_K_ratio": 2.0930,
            "P_K_ratio": 0.9767,
            "rain_temp_ratio": 9.7231,
        }
        adapter.predict_top_k(features, k=3)

        self.assertEqual(len(captured_input), 1)
        in_df = captured_input[0]
        self.assertEqual(in_df.shape, (1, 11))
        self.assertEqual(in_df.columns.tolist(), EXPECTED_MODEL_FEATURES)


if __name__ == "__main__":
    unittest.main()

