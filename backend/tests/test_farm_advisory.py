"""Comprehensive unit test suite for Phase 9 Evidence-Based Farm Advisory Engine."""

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
from app.services.farm_advisory import (
    ADVISORY_DISCLAIMER,
    CompatibilityStatus,
    CropAdvisoryItem,
    CropEnvironmentalRequirement,
    CropRequirementNotFoundError,
    CropRequirementRepository,
    DataQualityAudit,
    DEFAULT_ECOCROP_PROVENANCE,
    FAO_ECOCROP_PROFILES,
    FarmAdvisoryRequest,
    FarmAdvisoryResponse,
    FarmAdvisoryService,
    InvalidAdvisoryRequestError,
    RequirementProvenance,
    SatelliteEnvironmentalContext,
    VariableCompatibility,
    WaterAdvisory,
    WaterAdvisoryStatus,
    calculate_fao56_penman_monteith,
    classify_soil_texture_group,
    crop_requirement_repository,
    evaluate_crop_environmental_compatibility,
    evaluate_numeric_range,
    evaluate_soil_texture,
    evaluate_water_advisory,
    farm_advisory_service,
    generate_advisory_explanations,
    generate_advisory_limitations,
)
from app.services.farm_advisory.validators import (
    audit_data_freshness,
    validate_advisory_coordinates,
    validate_advisory_date,
)
from app.services.recommendation.schemas import (
    AgriculturalInput,
    CropRecommendationItem,
    DataQualityReport,
    EnvironmentalContext,
    RecommendationRequest,
    RecommendationResponse,
)


class TestCropRequirementProfiles(unittest.TestCase):
    """Test suite for authoritative FAO ECOCROP requirement profiles and repository."""

    def test_all_22_benchmark_crops_registered(self) -> None:
        """Verify that all 22 benchmark model crops are present in the repository."""
        expected_22 = [
            "apple",
            "banana",
            "blackgram",
            "chickpea",
            "coconut",
            "coffee",
            "cotton",
            "grapes",
            "jute",
            "kidneybeans",
            "lentil",
            "maize",
            "mango",
            "mothbeans",
            "mungbean",
            "muskmelon",
            "orange",
            "papaya",
            "pigeonpeas",
            "pomegranate",
            "rice",
            "watermelon",
        ]
        supported = crop_requirement_repository.list_supported_crops()
        for crop in expected_22:
            self.assertIn(crop, supported, f"Crop '{crop}' must be registered in FAO ECOCROP profiles.")
            req = crop_requirement_repository.get_requirement(crop)
            self.assertIsNotNone(req)
            self.assertIsNotNone(req.scientific_name)
            self.assertIsNotNone(req.ecocrop_code)
            self.assertIsNotNone(req.provenance)
            self.assertEqual(req.provenance.source_name, "FAO ECOCROP - Crop Ecological Requirements Database")

    def test_valid_crop_requirement_profile_rice(self) -> None:
        """Verify exact documented thresholds for rice (Oryza sativa, EcoCrop 1574)."""
        rice = crop_requirement_repository.get_requirement("rice")
        self.assertIsNotNone(rice)
        self.assertEqual(rice.crop_name, "rice")
        self.assertEqual(rice.scientific_name, "Oryza sativa")
        self.assertEqual(rice.ecocrop_code, 1574)
        self.assertEqual(rice.temp_opt_min_c, 20.0)
        self.assertEqual(rice.temp_opt_max_c, 30.0)
        self.assertEqual(rice.temp_min_c, 10.0)
        self.assertEqual(rice.temp_max_c, 36.0)
        self.assertEqual(rice.rainfall_opt_min_mm, 1500.0)
        self.assertEqual(rice.rainfall_opt_max_mm, 2000.0)
        self.assertEqual(rice.rainfall_min_mm, 1000.0)
        self.assertEqual(rice.rainfall_max_mm, 4000.0)
        self.assertEqual(rice.soil_ph_opt_min, 5.5)
        self.assertEqual(rice.soil_ph_opt_max, 7.0)
        self.assertEqual(rice.crop_cycle_min_days, 80)
        self.assertEqual(rice.crop_cycle_max_days, 180)

    def test_nullable_fields_preserved_without_guessing(self) -> None:
        """Verify that maize has nullable fields where authoritative data is not documented."""
        maize = crop_requirement_repository.get_requirement("maize")
        self.assertIsNotNone(maize)
        self.assertIsNone(maize.soil_textures_optimal)
        self.assertIsNone(maize.soil_drainage_optimal)

        watermelon = crop_requirement_repository.get_requirement("watermelon")
        self.assertIsNotNone(watermelon)
        self.assertIsNone(watermelon.crop_cycle_min_days)
        self.assertIsNone(watermelon.crop_cycle_max_days)

    def test_provenance_metadata_completeness(self) -> None:
        """Verify every profile has complete provenance metadata."""
        rice = crop_requirement_repository.get_requirement("rice")
        self.assertIsNotNone(rice.provenance.source_url)
        self.assertTrue(rice.provenance.source_url.startswith("https://"))
        self.assertIn("TOPMN", rice.provenance.source_field)
        self.assertIsNotNone(rice.provenance.notes)

    def test_missing_crop_lookup(self) -> None:
        """Verify lookup of unknown crop returns None without raising."""
        unknown = crop_requirement_repository.get_requirement("dragonfruit")
        self.assertIsNone(unknown)

    def test_register_and_remove_requirement(self) -> None:
        """Verify dynamic registration and removal for test isolation."""
        custom_repo = CropRequirementRepository()
        dummy = CropEnvironmentalRequirement(
            crop_name="testcrop",
            scientific_name="Testus cropus",
            ecocrop_code=99999,
            temp_opt_min_c=15.0,
            temp_opt_max_c=25.0,
            temp_min_c=5.0,
            temp_max_c=35.0,
            rainfall_opt_min_mm=500.0,
            rainfall_opt_max_mm=800.0,
            rainfall_min_mm=300.0,
            rainfall_max_mm=1200.0,
            soil_ph_opt_min=6.0,
            soil_ph_opt_max=7.0,
            soil_ph_min=5.0,
            soil_ph_max=8.0,
        )
        custom_repo.register_requirement(dummy)
        self.assertIsNotNone(custom_repo.get_requirement("testcrop"))
        custom_repo.remove_requirement("testcrop")
        self.assertIsNone(custom_repo.get_requirement("testcrop"))


class TestCompatibilityEngine(unittest.TestCase):
    """Test suite for deterministic compatibility checks against documented thresholds."""

    def test_temperature_favorable(self) -> None:
        """Test that observed temperature in optimal range yields favorable status."""
        eval_item = evaluate_numeric_range(
            variable_name="Temperature",
            observed=25.0,
            unit="°C",
            opt_min=20.0,
            opt_max=30.0,
            abs_min=10.0,
            abs_max=36.0,
        )
        self.assertEqual(eval_item.status, CompatibilityStatus.FAVORABLE)
        self.assertIn("falls within documented optimal range", eval_item.reason)
        self.assertEqual(eval_item.source, "FAO ECOCROP")

    def test_temperature_caution_below_optimum(self) -> None:
        """Test that temperature between absolute min and optimal min yields caution."""
        eval_item = evaluate_numeric_range(
            variable_name="Temperature",
            observed=15.0,
            unit="°C",
            opt_min=20.0,
            opt_max=30.0,
            abs_min=10.0,
            abs_max=36.0,
        )
        self.assertEqual(eval_item.status, CompatibilityStatus.CAUTION)
        self.assertIn("below optimal minimum", eval_item.reason)

    def test_temperature_caution_above_optimum(self) -> None:
        """Test that temperature between optimal max and absolute max yields caution."""
        eval_item = evaluate_numeric_range(
            variable_name="Temperature",
            observed=33.0,
            unit="°C",
            opt_min=20.0,
            opt_max=30.0,
            abs_min=10.0,
            abs_max=36.0,
        )
        self.assertEqual(eval_item.status, CompatibilityStatus.CAUTION)
        self.assertIn("above optimal maximum", eval_item.reason)

    def test_temperature_unfavorable_too_cold(self) -> None:
        """Test that temperature below absolute min yields unfavorable status."""
        eval_item = evaluate_numeric_range(
            variable_name="Temperature",
            observed=8.0,
            unit="°C",
            opt_min=20.0,
            opt_max=30.0,
            abs_min=10.0,
            abs_max=36.0,
        )
        self.assertEqual(eval_item.status, CompatibilityStatus.UNFAVORABLE)
        self.assertIn("below absolute minimum", eval_item.reason)

    def test_temperature_unfavorable_too_hot(self) -> None:
        """Test that temperature above absolute max yields unfavorable status."""
        eval_item = evaluate_numeric_range(
            variable_name="Temperature",
            observed=38.0,
            unit="°C",
            opt_min=20.0,
            opt_max=30.0,
            abs_min=10.0,
            abs_max=36.0,
        )
        self.assertEqual(eval_item.status, CompatibilityStatus.UNFAVORABLE)
        self.assertIn("above absolute maximum", eval_item.reason)

    def test_temperature_unavailable_missing_observed(self) -> None:
        """Test that missing observed temperature yields unavailable status."""
        eval_item = evaluate_numeric_range(
            variable_name="Temperature",
            observed=None,
            unit="°C",
            opt_min=20.0,
            opt_max=30.0,
            abs_min=10.0,
            abs_max=36.0,
        )
        self.assertEqual(eval_item.status, CompatibilityStatus.UNAVAILABLE)
        self.assertIn("unavailable", eval_item.reason)

    def test_rainfall_comparison(self) -> None:
        """Test rainfall comparison across favorable, caution, and unfavorable."""
        # Favorable
        fav = evaluate_numeric_range("Rainfall", 1600.0, "mm", 1500.0, 2000.0, 1000.0, 4000.0)
        self.assertEqual(fav.status, CompatibilityStatus.FAVORABLE)

        # Caution
        caut = evaluate_numeric_range("Rainfall", 1200.0, "mm", 1500.0, 2000.0, 1000.0, 4000.0)
        self.assertEqual(caut.status, CompatibilityStatus.CAUTION)

        # Unfavorable
        unfav = evaluate_numeric_range("Rainfall", 600.0, "mm", 1500.0, 2000.0, 1000.0, 4000.0)
        self.assertEqual(unfav.status, CompatibilityStatus.UNFAVORABLE)

    def test_soil_ph_comparison(self) -> None:
        """Test soil pH comparison across favorable, caution, and unfavorable."""
        # Favorable
        fav = evaluate_numeric_range("Soil pH", 6.5, "pH", 5.5, 7.0, 4.5, 9.0)
        self.assertEqual(fav.status, CompatibilityStatus.FAVORABLE)

        # Caution
        caut = evaluate_numeric_range("Soil pH", 5.0, "pH", 5.5, 7.0, 4.5, 9.0)
        self.assertEqual(caut.status, CompatibilityStatus.CAUTION)

        # Unfavorable
        unfav = evaluate_numeric_range("Soil pH", 3.8, "pH", 5.5, 7.0, 4.5, 9.0)
        self.assertEqual(unfav.status, CompatibilityStatus.UNFAVORABLE)

    def test_soil_texture_handling(self) -> None:
        """Test soil texture classification and compatibility checking."""
        # Heavy clay (clay=45%, sand=20%)
        heavy_eval = evaluate_soil_texture(
            clay_pct=45.0,
            sand_pct=20.0,
            silt_pct=35.0,
            opt_textures=["heavy", "medium"],
            abs_textures=["heavy", "medium", "light"],
        )
        self.assertEqual(heavy_eval.status, CompatibilityStatus.FAVORABLE)

        # Light sand (clay=10%, sand=88%)
        light_eval = evaluate_soil_texture(
            clay_pct=10.0,
            sand_pct=88.0,
            silt_pct=2.0,
            opt_textures=["heavy", "medium"],
            abs_textures=["heavy", "medium", "light"],
        )
        self.assertEqual(light_eval.status, CompatibilityStatus.CAUTION)

        # Unfavorable texture (light sand for crop that only tolerates heavy/medium)
        unfav_eval = evaluate_soil_texture(
            clay_pct=10.0,
            sand_pct=88.0,
            silt_pct=2.0,
            opt_textures=["heavy", "medium"],
            abs_textures=["heavy", "medium"],
        )
        self.assertEqual(unfav_eval.status, CompatibilityStatus.UNFAVORABLE)

        # Missing texture fractions
        missing_eval = evaluate_soil_texture(
            clay_pct=None,
            sand_pct=None,
            silt_pct=None,
            opt_textures=["medium"],
            abs_textures=["medium", "light"],
        )
        self.assertEqual(missing_eval.status, CompatibilityStatus.UNAVAILABLE)

    def test_limiting_factor_principle_overall_compatibility(self) -> None:
        """Test that overall status follows limiting factor principle without arbitrary percentages."""
        rice = crop_requirement_repository.get_requirement("rice")

        # All favorable
        status, evals, risks = evaluate_crop_environmental_compatibility(
            requirement=rice,
            temperature_c=25.0,
            rainfall_mm=1700.0,
            soil_ph=6.5,
            clay_pct=45.0,
            sand_pct=25.0,
            silt_pct=30.0,
        )
        self.assertEqual(status, CompatibilityStatus.FAVORABLE)
        self.assertEqual(len(risks), 0)

        # One factor caution -> overall caution
        status_c, _, risks_c = evaluate_crop_environmental_compatibility(
            requirement=rice,
            temperature_c=15.0,  # Caution
            rainfall_mm=1700.0,
            soil_ph=6.5,
            clay_pct=45.0,
            sand_pct=25.0,
            silt_pct=30.0,
        )
        self.assertEqual(status_c, CompatibilityStatus.CAUTION)
        self.assertIn("temperature_outside_documented_range", risks_c)

        # One factor unfavorable -> overall unfavorable
        status_u, _, risks_u = evaluate_crop_environmental_compatibility(
            requirement=rice,
            temperature_c=8.0,  # Unfavorable (< 10)
            rainfall_mm=1700.0,
            soil_ph=6.5,
            clay_pct=45.0,
            sand_pct=25.0,
            silt_pct=30.0,
        )
        self.assertEqual(status_u, CompatibilityStatus.UNFAVORABLE)
        self.assertIn("temperature_outside_documented_range", risks_u)


class TestWaterAdvisoryMethodology(unittest.TestCase):
    """Test suite for water advisory and FAO-56 methodology."""

    def test_water_advisory_unavailable_standard_weather(self) -> None:
        """Verify that standard weather lacking net radiation returns status 'unavailable'."""
        weather = WeatherResponse(
            latitude=16.2,
            longitude=77.35,
            temperature_c=28.4,
            humidity_percent=60.0,
            rainfall_mm=5.0,
            wind_speed_mps=3.2,
            weather_timestamp="2026-09-25T12:00",
        )
        advisory = evaluate_water_advisory(weather=weather)
        self.assertEqual(advisory.status, WaterAdvisoryStatus.UNAVAILABLE)
        self.assertIsNone(advisory.reference_evapotranspiration_et0_mm_day)
        self.assertIsNone(advisory.crop_evapotranspiration_etc_mm_day)
        self.assertIn("net_solar_radiation (Rn)", advisory.missing_parameters)
        self.assertIn("crop_growth_stage_coefficient (Kc)", advisory.missing_parameters)

    def test_water_advisory_available_with_complete_fao56_inputs(self) -> None:
        """Verify that supplying complete validated FAO-56 parameters computes ET0 and ETc."""
        fao_inputs = {
            "net_radiation_mj_m2_day": 14.5,
            "temp_mean_c": 24.5,
            "wind_speed_2m_mps": 2.1,
            "actual_vapor_pressure_kpa": 1.85,
            "saturation_vapor_pressure_kpa": 3.08,
            "psychrometric_constant_kpa_c": 0.067,
            "slope_vapor_pressure_curve_kpa_c": 0.185,
            "crop_coefficient_kc": 1.15,
            "effective_precipitation_mm": 2.0,
        }
        rice = crop_requirement_repository.get_requirement("rice")
        advisory = evaluate_water_advisory(
            weather=None,
            fao56_inputs=fao_inputs,
            crop_requirement=rice,
        )
        self.assertEqual(advisory.status, WaterAdvisoryStatus.AVAILABLE)
        self.assertIsNotNone(advisory.reference_evapotranspiration_et0_mm_day)
        self.assertGreater(advisory.reference_evapotranspiration_et0_mm_day, 0.0)
        self.assertIsNotNone(advisory.crop_evapotranspiration_etc_mm_day)
        self.assertIsNotNone(advisory.estimated_irrigation_requirement_mm)
        self.assertEqual(len(advisory.missing_parameters), 0)

    def test_exact_fao56_penman_monteith_calculation(self) -> None:
        """Verify mathematical calculation of FAO-56 Penman-Monteith."""
        et0 = calculate_fao56_penman_monteith(
            net_radiation_mj_m2_day=15.0,
            temp_mean_c=25.0,
            wind_speed_2m_mps=2.0,
            actual_vapor_pressure_kpa=1.70,
            saturation_vapor_pressure_kpa=3.17,
            psychrometric_constant_kpa_c=0.067,
            slope_vapor_pressure_curve_kpa_c=0.189,
        )
        self.assertIsInstance(et0, float)
        self.assertGreater(et0, 2.0)
        self.assertLess(et0, 10.0)


class TestValidatorsAndFreshness(unittest.TestCase):
    """Test suite for coordinate, date, and data freshness validation."""

    def test_valid_coordinates(self) -> None:
        """Verify valid coordinates pass."""
        lat, lon = validate_advisory_coordinates(16.2056, 77.3556)
        self.assertEqual(lat, 16.2056)
        self.assertEqual(lon, 77.3556)

    def test_invalid_coordinates(self) -> None:
        """Verify out-of-bounds coordinates raise InvalidAdvisoryRequestError."""
        with self.assertRaises(InvalidAdvisoryRequestError):
            validate_advisory_coordinates(95.0, 77.35)
        with self.assertRaises(InvalidAdvisoryRequestError):
            validate_advisory_coordinates(16.2, 195.0)

    def test_invalid_date_format(self) -> None:
        """Verify malformed date strings raise InvalidAdvisoryRequestError."""
        with self.assertRaises(InvalidAdvisoryRequestError):
            validate_advisory_date("2026-99-99")
        with self.assertRaises(InvalidAdvisoryRequestError):
            validate_advisory_date("not-a-date")

    def test_audit_data_freshness_flags_stale_weather(self) -> None:
        """Verify weather older than 7 days is audited as stale."""
        weather = WeatherResponse(
            latitude=16.2,
            longitude=77.35,
            temperature_c=28.4,
            humidity_percent=60.0,
            rainfall_mm=0.0,
            wind_speed_mps=3.2,
            weather_timestamp="2026-09-01T12:00",  # 24 days before target date
        )
        stale, warnings = audit_data_freshness(weather, None, "2026-09-25")
        self.assertIn("weather", stale)
        self.assertTrue(any("exceeding max freshness gap" in w for w in warnings))


class TestScientificLanguageAndTerminology(unittest.TestCase):
    """Verify strictly enforced scientific terminology and absence of forbidden phrases."""

    def test_scientific_terminology_enforced(self) -> None:
        """Verify explanations contain mandatory terminology and exclude forbidden phrases."""
        crop_advisories = [
            CropAdvisoryItem(
                crop="rice",
                scientific_name="Oryza sativa",
                rank=1,
                probability_estimate=0.88,
                confidence_percentage="88.00%",
                overall_compatibility=CompatibilityStatus.FAVORABLE,
                compatibility_evaluations={
                    "temperature": VariableCompatibility(
                        variable="Temperature",
                        status=CompatibilityStatus.FAVORABLE,
                        observed_value=26.5,
                        observed_unit="°C",
                        documented_optimal_range="20.0 to 30.0 °C",
                        documented_absolute_range="10.0 to 36.0 °C",
                        reason="Observed temperature falls within documented optimal range.",
                        source="FAO ECOCROP",
                    )
                },
                growth_cycle_days="80 to 180 days (FAO ECOCROP)",
                risk_flags=[],
                advisory_notes=["Management Note: Optimal planting window."],
                requirement_provenance=DEFAULT_ECOCROP_PROVENANCE,
            )
        ]
        water_adv = evaluate_water_advisory(None)
        data_quality = DataQualityAudit(
            model_available=True,
            weather_available=True,
            satellite_available=False,
            soil_available=True,
            missing_sources=["satellite"],
            stale_sources=[],
            risk_flags=["satellite_data_missing"],
            warnings=[],
        )

        explanations = generate_advisory_explanations(
            crop_advisories=crop_advisories,
            water_advisory=water_adv,
            satellite_context=None,
            data_quality=data_quality,
        )
        limitations = generate_advisory_limitations(
            crop_advisories=crop_advisories,
            data_quality=data_quality,
        )

        full_text = " ".join(explanations + limitations + [ADVISORY_DISCLAIMER]).lower()

        # Mandatory positive terminology
        self.assertIn("compatibility", full_text)
        self.assertIn("benchmark-model confidence estimate", full_text)
        self.assertIn("fao ecocrop", full_text)

        # Strictly forbidden marketing or exaggerated suitability terminology
        forbidden_terms = [
            "harvest success probability",
            "yield probability",
            "scientifically validated crop suitability percentage",
            "guaranteed crop recommendation",
            "guaranteed yield",
            "guaranteed harvest",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, full_text, f"Forbidden term '{term}' must not appear in advisory outputs.")


class TestFarmAdvisoryService(unittest.IsolatedAsyncioTestCase):
    """Integration test suite for FarmAdvisoryService."""

    async def test_generate_advisory_from_scratch(self) -> None:
        """Test full advisory generation workflow orchestrating recommendation and FAO checks."""
        request = FarmAdvisoryRequest(
            latitude=16.20,
            longitude=77.35,
            observation_date="2026-09-25",
            agricultural_inputs=AgriculturalInput(
                nitrogen=80.0,
                phosphorus=40.0,
                potassium=40.0,
                temperature=26.5,
                humidity=65.0,
                ph=6.8,
                rainfall=120.0,
            ),
            top_k=3,
            fetch_live_weather=False,
            fetch_live_satellite=False,
            fetch_live_soil=False,
        )

        response = await farm_advisory_service.generate_advisory(request)

        self.assertIsInstance(response, FarmAdvisoryResponse)
        self.assertEqual(len(response.crop_advisories), 3)

        # Check preserved ML probability estimates
        for item in response.crop_advisories:
            self.assertGreaterEqual(item.probability_estimate, 0.0)
            self.assertLessEqual(item.probability_estimate, 1.0)
            self.assertTrue(item.confidence_percentage.endswith("%"))
            self.assertIn(item.overall_compatibility, list(CompatibilityStatus))
            self.assertIsNotNone(item.requirement_provenance)

        # Check water advisory
        self.assertIsInstance(response.water_advisory, WaterAdvisory)
        self.assertEqual(response.water_advisory.status, WaterAdvisoryStatus.UNAVAILABLE)

        # Check risk flags
        self.assertIsInstance(response.risk_flags, list)
        self.assertIn("weather_data_missing", response.risk_flags)
        self.assertIn("satellite_data_missing", response.risk_flags)
        self.assertIn("soil_data_missing", response.risk_flags)

        # Check disclaimer
        self.assertEqual(response.disclaimer, ADVISORY_DISCLAIMER)

    async def test_generate_advisory_from_existing_phase8_response(self) -> None:
        """Test that passing a pre-computed RecommendationResponse avoids re-running inference."""
        dummy_rec = RecommendationResponse(
            latitude=16.2,
            longitude=77.35,
            observation_date="2026-09-25",
            recommendations=[
                CropRecommendationItem(
                    crop="rice",
                    rank=1,
                    probability_estimate=0.88,
                    confidence_percentage="88.00%",
                ),
                CropRecommendationItem(
                    crop="jute",
                    rank=2,
                    probability_estimate=0.08,
                    confidence_percentage="8.00%",
                ),
            ],
            environmental_context=EnvironmentalContext(
                weather=WeatherResponse(
                    latitude=16.2,
                    longitude=77.35,
                    temperature_c=25.0,
                    humidity_percent=70.0,
                    rainfall_mm=1600.0,
                    wind_speed_mps=2.5,
                    weather_timestamp="2026-09-25T12:00",
                ),
                satellite=None,
                soil=None,
            ),
            data_quality=DataQualityReport(
                model_available=True,
                weather_available=True,
                satellite_available=False,
                soil_available=False,
                missing_sources=["satellite", "soil"],
                warnings=[],
            ),
            explanation=["Benchmark model ranked rice."],
            limitations=["Benchmark model limitations."],
            model_input_features={},
        )

        request = FarmAdvisoryRequest(
            latitude=16.2,
            longitude=77.35,
            observation_date="2026-09-25",
            recommendation_response=dummy_rec,
        )

        # Mock the recommendation service to verify it is NOT called when pre-computed response is provided
        mock_rec_svc = MagicMock()
        mock_rec_svc.generate_recommendation = AsyncMock()
        advisory_svc = FarmAdvisoryService(rec_service=mock_rec_svc)

        response = await advisory_svc.generate_advisory(request)

        mock_rec_svc.generate_recommendation.assert_not_called()
        self.assertEqual(len(response.crop_advisories), 2)
        top_crop = response.crop_advisories[0]
        self.assertEqual(top_crop.crop, "rice")
        self.assertEqual(top_crop.probability_estimate, 0.88)
        self.assertEqual(top_crop.overall_compatibility, CompatibilityStatus.FAVORABLE)


class TestFarmAdvisoryApiEndpoint(unittest.IsolatedAsyncioTestCase):
    """Test suite for FastAPI route POST /api/advisory."""

    async def asyncSetUp(self) -> None:
        """Create async HTTP client for API route testing."""
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://test")

    async def asyncTearDown(self) -> None:
        """Close async HTTP client."""
        await self.client.aclose()

    async def test_api_advisory_success(self) -> None:
        """Test successful POST /api/advisory request."""
        payload = {
            "latitude": 16.20,
            "longitude": 77.35,
            "observation_date": "2026-09-25",
            "agricultural_inputs": {
                "nitrogen": 80.0,
                "phosphorus": 40.0,
                "potassium": 40.0,
                "temperature": 26.5,
                "humidity": 65.0,
                "ph": 6.8,
                "rainfall": 120.0,
            },
            "top_k": 3,
        }

        resp = await self.client.post("/api/advisory", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["latitude"], 16.2)
        self.assertEqual(data["longitude"], 77.35)
        self.assertIn("crop_advisories", data)
        self.assertEqual(len(data["crop_advisories"]), 3)
        self.assertIn("water_advisory", data)
        self.assertEqual(data["water_advisory"]["status"], "unavailable")
        self.assertIn("risk_flags", data)
        self.assertIn("explanations", data)
        self.assertIn("limitations", data)
        self.assertIn("disclaimer", data)

    async def test_api_advisory_invalid_coordinates(self) -> None:
        """Test POST /api/advisory with out-of-bounds latitude returns 422 or 400."""
        payload = {
            "latitude": 195.0,
            "longitude": 77.35,
            "nitrogen": 80.0,
            "phosphorus": 40.0,
            "potassium": 40.0,
            "temperature": 26.5,
            "humidity": 65.0,
            "ph": 6.8,
            "rainfall": 120.0,
        }
        resp = await self.client.post("/api/advisory", json=payload)
        self.assertIn(resp.status_code, (400, 422))

    async def test_api_advisory_missing_inputs(self) -> None:
        """Test POST /api/advisory with missing required agricultural inputs returns 400."""
        payload = {
            "latitude": 16.20,
            "longitude": 77.35,
        }
        resp = await self.client.post("/api/advisory", json=payload)
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
