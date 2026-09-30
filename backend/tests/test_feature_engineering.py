"""Comprehensive test suite for Phase 7 Multi-Source Feature Engineering.

Validates:
1. Valid unified feature construction across all four sources.
2. Missing weather data handling (preserved as None).
3. Missing satellite data handling (preserved as None).
4. Missing soil data handling (preserved as None).
5. Invalid latitude rejection (SpatialAlignmentError).
6. Invalid longitude rejection (SpatialAlignmentError).
7. Invalid temporal alignment rejection (TemporalAlignmentError).
8. Invalid satellite date window rejection (start > end).
9. Zero denominator protection for N/P ratio.
10. Zero denominator protection for N/K ratio.
11. Zero denominator protection for P/K ratio.
12. Zero crop label leakage into feature vector or prediction feature dict.
13. Complete exclusion of metadata from ML feature vector.
14. Deterministic feature vector consistency across repeated calls.
15. Unit consistency across environmental and pedological sources.
16. Unaltered satellite indices (no synthetic crop suitability conversion).
17. Preservation of soil depth interval and spatial resolution.
18. Preservation of satellite observation temporal window and scene counts.
19. Zero fabricated or synthetically imputed values for missing fields.
20. Immutability and integrity of the benchmark historical dataset.
Plus cross-source spatial mismatch detection and machine-readable schema validation.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.schemas.weather import WeatherResponse
from app.schemas.satellite import SatelliteResponse
from app.schemas.soil import SoilResponse, SoilProperties
from app.services.feature_engineering import (
    MultiSourceFeatureBuilder,
    feature_builder,
    MultiSourceObservation,
    MultiSourceFeatureVector,
    FEATURE_COLUMN_ORDER,
    SpatialAlignmentError,
    TemporalAlignmentError,
    DataLeakageError,
    safe_ratio,
    validate_coordinates,
    validate_satellite_date_window,
    validate_temporal_alignment,
    validate_no_target_leakage,
)


class TestMultiSourceFeatureEngineering(unittest.TestCase):
    """Test suite covering the 20 Phase 7 feature engineering requirements."""

    def setUp(self) -> None:
        """Construct canonical mock response fixtures for clean multi-source testing."""
        self.builder = MultiSourceFeatureBuilder()
        self.target_lat = 16.20
        self.target_lon = 77.35
        self.obs_date = "2026-09-25"


        # Mock authentic WeatherResponse fixture
        self.mock_weather = WeatherResponse(
            latitude=16.20,
            longitude=77.35,
            temperature_c=28.4,
            humidity_percent=64.0,
            rainfall_mm=12.5,
            wind_speed_mps=3.2,
            weather_timestamp="2026-09-25T17:15",
        )

        # Mock authentic SatelliteResponse fixture
        self.mock_satellite = SatelliteResponse(
            latitude=16.20,
            longitude=77.35,
            radius_m=500.0,
            start_date="2026-09-10",
            end_date="2026-09-25",
            usable_observations=4,
            cloud_probability_threshold=65.0,
            ndvi_median=0.62,
            ndwi_median=0.15,
            ndmi_median=0.28,
            data_source="Sentinel-2",
        )

        # Mock authentic SoilResponse fixture
        self.mock_soil = SoilResponse(
            latitude=16.20,
            longitude=77.35,
            depth_interval="0-5cm",
            soil=SoilProperties(
                ph=6.8,
                clay_pct=34.2,
                sand_pct=28.5,
                silt_pct=37.3,
                organic_carbon_g_kg=14.5,
                bulk_density=1.45,
                cec=24.8,
                nitrogen_g_kg=1.25,
            ),
            data_source="ISRIC SoilGrids 2.0",
            resolution_m=250,
        )

        # Mock historical agricultural sample
        self.mock_agri = {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "temperature": 25.5,
            "humidity": 70.0,
            "ph": 6.5,
            "rainfall": 150.0,
            "label": "rice",
        }

    # -------------------------------------------------------------------------
    # Requirement 1: Valid unified feature construction
    # -------------------------------------------------------------------------
    def test_01_valid_unified_feature_construction(self) -> None:
        """Verify unified multi-source observation builds correctly from all 4 sources."""
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            observation_date=self.obs_date,
            weather=self.mock_weather,
            satellite=self.mock_satellite,
            soil=self.mock_soil,
            agricultural_data=self.mock_agri,
        )

        self.assertIsInstance(obs, MultiSourceObservation)
        self.assertEqual(obs.metadata.latitude, self.target_lat)
        self.assertEqual(obs.metadata.longitude, self.target_lon)
        self.assertEqual(obs.metadata.observation_date, self.obs_date)

        # Agricultural values
        self.assertEqual(obs.agricultural.nitrogen, 90.0)
        self.assertEqual(obs.agricultural.phosphorus, 42.0)
        self.assertEqual(obs.agricultural.potassium, 43.0)

        # Weather values
        self.assertEqual(obs.weather.weather_temperature, 28.4)
        self.assertEqual(obs.weather.weather_precipitation, 12.5)

        # Satellite values
        self.assertEqual(obs.satellite.satellite_ndvi, 0.62)
        self.assertEqual(obs.satellite.satellite_usable_observations, 4)

        # Soil values
        self.assertEqual(obs.soil.soil_ph, 6.8)
        self.assertEqual(obs.soil.soil_depth_interval, "0-5cm")

        # Derived nutrient ratios
        self.assertAlmostEqual(obs.derived.n_p_ratio, 90.0 / 42.0, places=3)
        self.assertAlmostEqual(obs.derived.n_k_ratio, 90.0 / 43.0, places=3)

        # Target label preserved
        self.assertEqual(obs.crop_label, "rice")

    # -------------------------------------------------------------------------
    # Requirement 2: Missing weather data
    # -------------------------------------------------------------------------
    def test_02_missing_weather_data(self) -> None:
        """Verify pipeline handles missing weather data without crashing, preserving None."""
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            observation_date=self.obs_date,
            weather=None,
            satellite=self.mock_satellite,
            soil=self.mock_soil,
            agricultural_data=self.mock_agri,
        )

        self.assertIsNone(obs.weather.weather_temperature)
        self.assertIsNone(obs.weather.weather_humidity)
        self.assertIsNone(obs.weather.weather_precipitation)
        self.assertIsNone(obs.weather.weather_wind_speed)
        self.assertIsNone(obs.weather.weather_timestamp)

        # Other sources must remain fully populated
        self.assertEqual(obs.satellite.satellite_ndvi, 0.62)
        self.assertEqual(obs.soil.soil_ph, 6.8)
        self.assertEqual(obs.agricultural.nitrogen, 90.0)

    # -------------------------------------------------------------------------
    # Requirement 3: Missing satellite data
    # -------------------------------------------------------------------------
    def test_03_missing_satellite_data(self) -> None:
        """Verify pipeline handles missing satellite data without crashing, preserving None."""
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            observation_date=self.obs_date,
            weather=self.mock_weather,
            satellite=None,
            soil=self.mock_soil,
            agricultural_data=self.mock_agri,
        )

        self.assertIsNone(obs.satellite.satellite_ndvi)
        self.assertIsNone(obs.satellite.satellite_ndwi)
        self.assertIsNone(obs.satellite.satellite_ndmi)
        self.assertIsNone(obs.satellite.satellite_usable_observations)

        # Weather and Soil remain intact
        self.assertEqual(obs.weather.weather_temperature, 28.4)
        self.assertEqual(obs.soil.soil_ph, 6.8)

    # -------------------------------------------------------------------------
    # Requirement 4: Missing soil data
    # -------------------------------------------------------------------------
    def test_04_missing_soil_data(self) -> None:
        """Verify pipeline handles missing soil data without crashing, preserving None."""
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            observation_date=self.obs_date,
            weather=self.mock_weather,
            satellite=self.mock_satellite,
            soil=None,
            agricultural_data=self.mock_agri,
        )

        self.assertIsNone(obs.soil.soil_ph)
        self.assertIsNone(obs.soil.soil_clay_pct)
        self.assertIsNone(obs.soil.soil_organic_carbon_g_kg)
        self.assertIsNone(obs.soil.soil_depth_interval)

        # Weather and Satellite remain intact
        self.assertEqual(obs.weather.weather_temperature, 28.4)
        self.assertEqual(obs.satellite.satellite_ndvi, 0.62)

    # -------------------------------------------------------------------------
    # Requirement 5: Invalid latitude
    # -------------------------------------------------------------------------
    def test_05_invalid_latitude(self) -> None:
        """Verify latitude outside [-90.0, 90.0] raises SpatialAlignmentError."""
        with self.assertRaises(SpatialAlignmentError):
            self.builder.build_unified_observation(
                latitude=95.0,
                longitude=77.35,
            )

        with self.assertRaises(SpatialAlignmentError):
            self.builder.build_unified_observation(
                latitude=-91.5,
                longitude=77.35,
            )

    # -------------------------------------------------------------------------
    # Requirement 6: Invalid longitude
    # -------------------------------------------------------------------------
    def test_06_invalid_longitude(self) -> None:
        """Verify longitude outside [-180.0, 180.0] raises SpatialAlignmentError."""
        with self.assertRaises(SpatialAlignmentError):
            self.builder.build_unified_observation(
                latitude=16.20,
                longitude=185.0,
            )

        with self.assertRaises(SpatialAlignmentError):
            self.builder.build_unified_observation(
                latitude=16.20,
                longitude=-181.0,
            )

    # -------------------------------------------------------------------------
    # Requirement 7: Invalid temporal alignment
    # -------------------------------------------------------------------------
    def test_07_invalid_temporal_alignment(self) -> None:
        """Verify incompatible temporal combinations are rejected rather than silently joined."""
        # Weather observation from 2026-09-25 cannot legitimately join with an observation_date of 2026-05-01
        with self.assertRaises(TemporalAlignmentError):
            self.builder.build_unified_observation(
                latitude=self.target_lat,
                longitude=self.target_lon,
                observation_date="2026-05-01",
                weather=self.mock_weather,  # timestamp 2026-09-25T17:15
                strict_temporal=True,
            )

        # Satellite window from 2024 cannot join an observation date in 2026
        satellite_old = SatelliteResponse(
            latitude=16.20,
            longitude=77.35,
            radius_m=500.0,
            start_date="2024-01-01",
            end_date="2024-01-15",
            usable_observations=2,
            cloud_probability_threshold=65.0,
            ndvi_median=0.45,
            ndwi_median=0.10,
            ndmi_median=0.20,
        )
        with self.assertRaises(TemporalAlignmentError):
            self.builder.build_unified_observation(
                latitude=self.target_lat,
                longitude=self.target_lon,
                observation_date="2026-09-25",
                satellite=satellite_old,
                strict_temporal=True,
            )

    # -------------------------------------------------------------------------
    # Requirement 8: Invalid satellite date window
    # -------------------------------------------------------------------------
    def test_08_invalid_satellite_date_window(self) -> None:
        """Verify satellite date window with start_date > end_date raises error."""
        with self.assertRaises(TemporalAlignmentError):
            validate_satellite_date_window("2026-09-25", "2026-09-01")

        with self.assertRaises(TemporalAlignmentError):
            self.builder.build_unified_observation(
                latitude=self.target_lat,
                longitude=self.target_lon,
                satellite={
                    "latitude": 16.20,
                    "longitude": 77.35,
                    "start_date": "2026-09-25",
                    "end_date": "2026-09-10",
                    "ndvi_median": 0.5,
                },
            )

    # -------------------------------------------------------------------------
    # Requirement 9: Zero denominator N/P
    # -------------------------------------------------------------------------
    def test_09_zero_denominator_n_p(self) -> None:
        """Verify N/P ratio evaluates safely to None when P <= 0 or missing, with no crash."""
        self.assertIsNone(safe_ratio(80.0, 0.0))
        self.assertIsNone(safe_ratio(80.0, -5.0))
        self.assertIsNone(safe_ratio(80.0, None))

        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            agricultural_data={"N": 80.0, "P": 0.0, "K": 40.0},
        )
        self.assertIsNone(obs.derived.n_p_ratio)
        self.assertIsNotNone(obs.derived.n_k_ratio)

    # -------------------------------------------------------------------------
    # Requirement 10: Zero denominator N/K
    # -------------------------------------------------------------------------
    def test_10_zero_denominator_n_k(self) -> None:
        """Verify N/K ratio evaluates safely to None when K <= 0 or missing, with no crash."""
        self.assertIsNone(safe_ratio(80.0, 0.0))
        self.assertIsNone(safe_ratio(80.0, -10.0))

        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            agricultural_data={"N": 80.0, "P": 40.0, "K": 0.0},
        )
        self.assertIsNone(obs.derived.n_k_ratio)
        self.assertIsNotNone(obs.derived.n_p_ratio)

    # -------------------------------------------------------------------------
    # Requirement 11: Zero denominator P/K
    # -------------------------------------------------------------------------
    def test_11_zero_denominator_p_k(self) -> None:
        """Verify P/K ratio evaluates safely to None when K <= 0 or missing, with no crash."""
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            agricultural_data={"N": 80.0, "P": 40.0, "K": 0.0},
        )
        self.assertIsNone(obs.derived.p_k_ratio)

    # -------------------------------------------------------------------------
    # Requirement 12: No crop label leakage into feature vector
    # -------------------------------------------------------------------------
    def test_12_no_crop_label_leakage_into_feature_vector(self) -> None:
        """Verify crop label is strictly excluded from predictive feature dictionary and vector."""
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            agricultural_data=self.mock_agri,
            crop_label="rice",
        )

        # Feature dictionary for ML inference
        feat_dict = obs.to_feature_dict(include_target=False)
        self.assertNotIn("crop_label", feat_dict)
        self.assertNotIn("label", feat_dict)
        self.assertNotIn("target_crop_label", feat_dict)

        # Feature vector for ML inference
        feat_vector = obs.to_feature_vector()
        self.assertEqual(len(feat_vector), len(FEATURE_COLUMN_ORDER))
        # Ensure all items in vector are numbers or None, absolutely no string labels
        for val in feat_vector:
            self.assertTrue(val is None or isinstance(val, (int, float)))

        # Validator raises if leakage attempted
        with self.assertRaises(DataLeakageError):
            validate_no_target_leakage({"nitrogen": 50.0, "crop_label": "rice"})

        with self.assertRaises(DataLeakageError):
            validate_no_target_leakage({"nitrogen": 50.0, "label": "rice"})

    # -------------------------------------------------------------------------
    # Requirement 13: Metadata excluded from feature vector
    # -------------------------------------------------------------------------
    def test_13_metadata_excluded_from_feature_vector(self) -> None:
        """Verify geospatial coordinates, dates, and provider tags are excluded from feature vector."""
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            observation_date=self.obs_date,
            weather=self.mock_weather,
            satellite=self.mock_satellite,
            soil=self.mock_soil,
            agricultural_data=self.mock_agri,
        )

        feat_dict = obs.to_feature_dict(include_target=False, include_metadata=False)

        excluded_metadata = [
            "latitude",
            "longitude",
            "observation_date",
            "location_source",
            "weather_timestamp",
            "satellite_start_date",
            "satellite_end_date",
            "satellite_radius_m",
            "soil_depth_interval",
            "soil_resolution_m",
            "data_sources",
            "disclaimer",
        ]
        for meta_key in excluded_metadata:
            self.assertNotIn(meta_key, feat_dict)

        # Confirm length matches FEATURE_COLUMN_ORDER
        self.assertEqual(len(feat_dict), len(FEATURE_COLUMN_ORDER))

    # -------------------------------------------------------------------------
    # Requirement 14: Deterministic feature vector
    # -------------------------------------------------------------------------
    def test_14_deterministic_feature_vector(self) -> None:
        """Verify repeated feature vector extractions produce identical values and ordering."""
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            observation_date=self.obs_date,
            weather=self.mock_weather,
            satellite=self.mock_satellite,
            soil=self.mock_soil,
            agricultural_data=self.mock_agri,
        )

        v1 = obs.to_feature_vector()
        v2 = obs.to_feature_vector()
        v3 = self.builder.to_feature_vector(obs)

        self.assertEqual(v1, v2)
        self.assertEqual(v2, v3)
        self.assertEqual(self.builder.get_feature_names(), FEATURE_COLUMN_ORDER)

    # -------------------------------------------------------------------------
    # Requirement 15: Unit consistency
    # -------------------------------------------------------------------------
    def test_15_unit_consistency(self) -> None:
        """Verify units are preserved consistently according to agronomic and scientific standards."""
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            weather=self.mock_weather,
            soil=self.mock_soil,
            agricultural_data=self.mock_agri,
        )

        # Weather: Celsius, %, mm, m/s
        self.assertEqual(obs.weather.weather_temperature, 28.4)  # °C
        self.assertEqual(obs.weather.weather_humidity, 64.0)     # %
        self.assertEqual(obs.weather.weather_precipitation, 12.5) # mm
        self.assertEqual(obs.weather.weather_wind_speed, 3.2)    # m/s

        # Soil: pH 0-14, clay/sand/silt %, SOC g/kg, bulk density kg/dm³, CEC cmol/kg
        self.assertEqual(obs.soil.soil_ph, 6.8)
        self.assertEqual(obs.soil.soil_clay_pct, 34.2)
        self.assertEqual(obs.soil.soil_sand_pct, 28.5)
        self.assertEqual(obs.soil.soil_silt_pct, 37.3)
        self.assertEqual(obs.soil.soil_organic_carbon_g_kg, 14.5)
        self.assertEqual(obs.soil.soil_bulk_density, 1.45)
        self.assertEqual(obs.soil.soil_cec, 24.8)
        self.assertEqual(obs.soil.soil_nitrogen_g_kg, 1.25)

    # -------------------------------------------------------------------------
    # Requirement 16: Satellite indices remain unchanged
    # -------------------------------------------------------------------------
    def test_16_satellite_indices_remain_unchanged(self) -> None:
        """Verify satellite indices (NDVI, NDWI, NDMI) preserve their authentic values and definitions."""
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            satellite=self.mock_satellite,
        )

        self.assertEqual(obs.satellite.satellite_ndvi, 0.62)
        self.assertEqual(obs.satellite.satellite_ndwi, 0.15)
        self.assertEqual(obs.satellite.satellite_ndmi, 0.28)
        # Ensure values fall within canonical [-1.0, 1.0] range
        for idx in [obs.satellite.satellite_ndvi, obs.satellite.satellite_ndwi, obs.satellite.satellite_ndmi]:
            self.assertTrue(-1.0 <= idx <= 1.0)

    # -------------------------------------------------------------------------
    # Requirement 17: Soil depth preserved
    # -------------------------------------------------------------------------
    def test_17_soil_depth_preserved(self) -> None:
        """Verify soil depth interval (0-5cm) and spatial resolution (250m) are explicitly preserved."""
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            soil=self.mock_soil,
        )

        self.assertEqual(obs.soil.soil_depth_interval, "0-5cm")
        self.assertEqual(obs.soil.soil_resolution_m, 250)

    # -------------------------------------------------------------------------
    # Requirement 18: Satellite observation window preserved
    # -------------------------------------------------------------------------
    def test_18_satellite_observation_window_preserved(self) -> None:
        """Verify satellite observation window start/end and scene counts are preserved."""
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            satellite=self.mock_satellite,
        )

        self.assertEqual(obs.satellite.satellite_start_date, "2026-09-10")
        self.assertEqual(obs.satellite.satellite_end_date, "2026-09-25")
        self.assertEqual(obs.satellite.satellite_usable_observations, 4)
        self.assertEqual(obs.satellite.satellite_cloud_probability_threshold, 65.0)

    # -------------------------------------------------------------------------
    # Requirement 19: No fabricated values
    # -------------------------------------------------------------------------
    def test_19_no_fabricated_values(self) -> None:
        """Verify missing attributes remain None and are never silently replaced with 0 or synthetic averages."""
        # Empty observation with only coordinates
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
        )

        # Check that unprovided fields are strictly None, NOT 0.0 or synthetic means
        self.assertIsNone(obs.agricultural.nitrogen)
        self.assertIsNone(obs.agricultural.historical_rainfall)
        self.assertIsNone(obs.weather.weather_temperature)
        self.assertIsNone(obs.weather.weather_precipitation)
        self.assertIsNone(obs.satellite.satellite_ndvi)
        self.assertIsNone(obs.soil.soil_ph)
        self.assertIsNone(obs.soil.soil_clay_pct)
        self.assertIsNone(obs.derived.n_p_ratio)

        feat_vector = obs.to_feature_vector()
        self.assertTrue(all(v is None for v in feat_vector))

    # -------------------------------------------------------------------------
    # Requirement 20: Historical dataset remains unchanged
    # -------------------------------------------------------------------------
    def test_20_historical_dataset_remains_unchanged(self) -> None:
        """Verify the raw historical dataset file is strictly preserved without mutation."""
        raw_csv_path = BASE_DIR / "data" / "raw" / "Crop_recommendation.csv"
        self.assertTrue(raw_csv_path.exists(), f"Raw CSV missing at {raw_csv_path}")

        df = pd.read_csv(raw_csv_path)
        self.assertEqual(len(df), 2200, "Historical dataset row count must remain exactly 2,200")
        self.assertEqual(
            list(df.columns),
            ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "label"],
            "Historical dataset columns must remain strictly unaltered",
        )
        self.assertEqual(df["label"].nunique(), 22, "Historical classes must remain 22")
        self.assertEqual(df.isnull().sum().sum(), 0, "Historical dataset must have zero nulls")

    # -------------------------------------------------------------------------
    # Additional Robustness: Cross-source spatial alignment verification
    # -------------------------------------------------------------------------
    def test_cross_source_spatial_mismatch_detection(self) -> None:
        """Verify spatial mismatch between sources (e.g. Weather from Delhi and Satellite from Bangalore) is caught."""
        # Mismatched weather from different coordinates (Delhi ~28.61, 77.20)
        mismatched_weather = WeatherResponse(
            latitude=28.61,
            longitude=77.20,
            temperature_c=32.0,
            humidity_percent=45.0,
            rainfall_mm=0.0,
            wind_speed_mps=2.1,
            weather_timestamp="2026-09-25T17:15",
        )

        with self.assertRaises(SpatialAlignmentError):
            self.builder.build_unified_observation(
                latitude=self.target_lat,  # 16.20
                longitude=self.target_lon, # 77.35
                weather=mismatched_weather,
                strict_spatial=True,
            )

    # -------------------------------------------------------------------------
    # Additional Robustness: Machine-readable schema metadata verification
    # -------------------------------------------------------------------------
    def test_multisource_feature_schema_json_integrity(self) -> None:
        """Verify multisource_feature_schema.json documents all 27 features and includes integrity statement."""
        schema_path = BASE_DIR / "ml" / "datasets" / "multisource_feature_schema.json"
        self.assertTrue(schema_path.exists(), f"Schema file missing at {schema_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        self.assertEqual(schema["feature_count"], 27)
        self.assertEqual(len(schema["features"]), 27)

        documented_names = [feat["name"] for feat in schema["features"]]
        self.assertEqual(documented_names, FEATURE_COLUMN_ORDER)

        # Verify integrity and anti-fabrication statement
        self.assertIn("data_integrity_statement", schema)
        self.assertIn("benchmark agricultural dataset lacks", schema["data_integrity_statement"])

    # -------------------------------------------------------------------------
    # Additional Robustness: Configurable spatial tolerance verification
    # -------------------------------------------------------------------------
    def test_configurable_spatial_tolerance(self) -> None:
        """Verify spatial tolerance is configurable: rejects at default 0.005° (~550m), accepts at 0.01°."""
        # Coordinate shifted by 0.007° (~770m)
        slightly_shifted_weather = WeatherResponse(
            latitude=16.207,
            longitude=77.35,
            temperature_c=28.4,
            humidity_percent=64.0,
            rainfall_mm=0.0,
            wind_speed_mps=3.0,
            weather_timestamp="2026-09-25T17:15",
        )

        # Default tolerance 0.005° should reject 0.007° difference
        with self.assertRaises(SpatialAlignmentError):
            self.builder.build_unified_observation(
                latitude=self.target_lat,
                longitude=self.target_lon,
                weather=slightly_shifted_weather,
                strict_spatial=True,
            )

        # Overriding tolerance to 0.01° should accept 0.007° difference
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            weather=slightly_shifted_weather,
            strict_spatial=True,
            spatial_tolerance_deg=0.01,
        )
        self.assertIsNotNone(obs)
        self.assertEqual(obs.metadata.spatial_tolerance_deg, 0.01)

    # -------------------------------------------------------------------------
    # Additional Robustness: Temporal future leakage rejection
    # -------------------------------------------------------------------------
    def test_temporal_future_leakage_rejection(self) -> None:
        """Verify that satellite imagery from the future relative to observation date is strictly rejected."""
        # Planting date is 2026-09-01, but satellite window is 2026-09-10 to 2026-09-25 (future observation)
        with self.assertRaises(TemporalAlignmentError) as ctx:
            self.builder.build_unified_observation(
                latitude=self.target_lat,
                longitude=self.target_lon,
                observation_date="2026-09-01",
                satellite=self.mock_satellite,  # start: 2026-09-10
                strict_temporal=True,
            )
        self.assertIn("Future data leakage detected", str(ctx.exception))

    # -------------------------------------------------------------------------
    # Additional Robustness: Configurable temporal tolerance verification
    # -------------------------------------------------------------------------
    def test_configurable_temporal_tolerances(self) -> None:
        """Verify temporal margins are configurable: rejects outside default 14-day window, accepts with override."""
        # Satellite window ending 18 days prior to observation date
        satellite_stale = SatelliteResponse(
            latitude=16.20,
            longitude=77.35,
            radius_m=500.0,
            start_date="2026-08-20",
            end_date="2026-09-07",  # 18 days before 2026-09-25
            usable_observations=3,
            cloud_probability_threshold=65.0,
            ndvi_median=0.58,
            ndwi_median=0.12,
            ndmi_median=0.22,
        )

        # Default 14-day margin rejects 18-day gap
        with self.assertRaises(TemporalAlignmentError):
            self.builder.build_unified_observation(
                latitude=self.target_lat,
                longitude=self.target_lon,
                observation_date="2026-09-25",
                satellite=satellite_stale,
                strict_temporal=True,
            )

        # Overriding satellite_max_window_days to 20 accepts 18-day gap
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            observation_date="2026-09-25",
            satellite=satellite_stale,
            strict_temporal=True,
            satellite_max_window_days=20,
        )
        self.assertIsNotNone(obs)

    # =========================================================================
    # Explicit Temporal Leakage Tests (User Audit Requirements)
    # =========================================================================

    def test_leakage_1_satellite_end_date_after_observation_date_rejected(self) -> None:
        """1. Satellite end date after observation date must be rejected (leakage)."""
        satellite = SatelliteResponse(
            latitude=self.target_lat,
            longitude=self.target_lon,
            radius_m=500.0,
            start_date="2026-09-01",
            end_date="2026-09-15",
            usable_observations=3,
            cloud_probability_threshold=65.0,
            ndvi_median=0.55,
            ndwi_median=0.15,
            ndmi_median=0.25,
        )
        with self.assertRaises(TemporalAlignmentError) as ctx:
            self.builder.build_unified_observation(
                latitude=self.target_lat,
                longitude=self.target_lon,
                observation_date="2026-09-10",  # satellite_end (09-15) > obs (09-10)
                satellite=satellite,
                strict_temporal=True,
            )
        self.assertIn("Future data leakage detected", str(ctx.exception))
        self.assertIn("must end on or before the observation date", str(ctx.exception))

    def test_leakage_2_satellite_start_before_and_end_after_observation_date_rejected(self) -> None:
        """2. Satellite start before observation date AND end after observation date must be rejected."""
        satellite = SatelliteResponse(
            latitude=self.target_lat,
            longitude=self.target_lon,
            radius_m=500.0,
            start_date="2026-08-25",  # before obs date
            end_date="2026-09-12",    # after obs date (future leakage)
            usable_observations=4,
            cloud_probability_threshold=65.0,
            ndvi_median=0.58,
            ndwi_median=0.14,
            ndmi_median=0.26,
        )
        with self.assertRaises(TemporalAlignmentError) as ctx:
            self.builder.build_unified_observation(
                latitude=self.target_lat,
                longitude=self.target_lon,
                observation_date="2026-09-10",
                satellite=satellite,
                strict_temporal=True,
            )
        self.assertIn("Future data leakage detected", str(ctx.exception))

    def test_leakage_3_satellite_window_entirely_before_or_on_observation_date_accepted(self) -> None:
        """3. Satellite window entirely before/on observation date must be accepted."""
        satellite = SatelliteResponse(
            latitude=self.target_lat,
            longitude=self.target_lon,
            radius_m=500.0,
            start_date="2026-08-27",
            end_date="2026-09-10",  # ends exactly on observation date
            usable_observations=3,
            cloud_probability_threshold=65.0,
            ndvi_median=0.60,
            ndwi_median=0.16,
            ndmi_median=0.27,
        )
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            observation_date="2026-09-10",
            satellite=satellite,
            strict_temporal=True,
        )
        self.assertIsNotNone(obs)
        self.assertEqual(obs.satellite.satellite_end_date, "2026-09-10")

    def test_leakage_4_weather_timestamp_after_observation_date_rejected(self) -> None:
        """4. Weather timestamp after observation date must be rejected (leakage)."""
        future_weather = WeatherResponse(
            latitude=self.target_lat,
            longitude=self.target_lon,
            temperature_c=29.0,
            humidity_percent=60.0,
            rainfall_mm=0.0,
            wind_speed_mps=3.1,
            weather_timestamp="2026-09-11T10:00",  # 1 day after obs date
        )
        with self.assertRaises(TemporalAlignmentError) as ctx:
            self.builder.build_unified_observation(
                latitude=self.target_lat,
                longitude=self.target_lon,
                observation_date="2026-09-10",
                weather=future_weather,
                strict_temporal=True,
            )
        self.assertIn("Future data leakage detected", str(ctx.exception))
        self.assertIn("cannot occur in the future", str(ctx.exception))

    def test_leakage_5_weather_timestamp_exactly_on_observation_date_accepted(self) -> None:
        """5. Weather timestamp exactly on observation date must be accepted."""
        same_day_weather = WeatherResponse(
            latitude=self.target_lat,
            longitude=self.target_lon,
            temperature_c=28.4,
            humidity_percent=64.0,
            rainfall_mm=5.0,
            wind_speed_mps=3.2,
            weather_timestamp="2026-09-10T16:45",
        )
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            observation_date="2026-09-10",
            weather=same_day_weather,
            strict_temporal=True,
        )
        self.assertIsNotNone(obs)
        self.assertEqual(obs.weather.weather_temperature, 28.4)

    def test_leakage_6_weather_timestamp_within_allowed_historical_gap_accepted(self) -> None:
        """6. Weather timestamp within allowed historical gap (e.g., 3 days prior <= 7 days) must be accepted."""
        recent_weather = WeatherResponse(
            latitude=self.target_lat,
            longitude=self.target_lon,
            temperature_c=27.5,
            humidity_percent=62.0,
            rainfall_mm=1.0,
            wind_speed_mps=2.8,
            weather_timestamp="2026-09-07T12:00",  # 3 days prior, within default 7-day gap
        )
        obs = self.builder.build_unified_observation(
            latitude=self.target_lat,
            longitude=self.target_lon,
            observation_date="2026-09-10",
            weather=recent_weather,
            strict_temporal=True,
        )
        self.assertIsNotNone(obs)
        self.assertEqual(obs.weather.weather_temperature, 27.5)

    def test_leakage_7_weather_timestamp_older_than_configured_gap_rejected(self) -> None:
        """7. Weather timestamp older than configured gap (e.g. 9 days prior > 7 days) must be rejected."""
        stale_weather = WeatherResponse(
            latitude=self.target_lat,
            longitude=self.target_lon,
            temperature_c=26.0,
            humidity_percent=58.0,
            rainfall_mm=0.0,
            wind_speed_mps=2.5,
            weather_timestamp="2026-09-01T12:00",  # 9 days prior, exceeds 7 days
        )
        with self.assertRaises(TemporalAlignmentError) as ctx:
            self.builder.build_unified_observation(
                latitude=self.target_lat,
                longitude=self.target_lon,
                observation_date="2026-09-10",
                weather=stale_weather,
                strict_temporal=True,
            )
        self.assertIn("exceeding allowable engineering gap of 7 days", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()


