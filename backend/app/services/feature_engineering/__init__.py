"""Multi-Source Feature Engineering module for AgriSense AI.

Provides a clean, reproducible, and leakage-free architecture for normalizing, aligning,
and engineering multi-source features across historical agricultural data, live weather,
Sentinel-2 satellite indicators, and ISRIC SoilGrids pedological context.
"""

from app.services.feature_engineering.schemas import (
    FEATURE_COLUMN_ORDER,
    AlignmentMetadata,
    AgriculturalFeatures,
    WeatherFeatures,
    SatelliteFeatures,
    SoilFeatures,
    DerivedAgronomicFeatures,
    MultiSourceObservation,
    MultiSourceFeatureVector,
)
from app.services.feature_engineering.normalizer import (
    normalize_weather_response,
    normalize_satellite_response,
    normalize_soil_response,
    normalize_agricultural_data,
)
from app.services.feature_engineering.validators import (
    FeatureEngineeringError,
    SpatialAlignmentError,
    TemporalAlignmentError,
    DataLeakageError,
    DataIntegrityError,
    validate_coordinates,
    validate_cross_source_spatial_alignment,
    validate_satellite_date_window,
    validate_temporal_alignment,
    validate_no_target_leakage,
    safe_ratio,
    parse_iso_date,
)
from app.services.feature_engineering.builder import (
    MultiSourceFeatureBuilder,
    feature_builder,
)

__all__ = [
    "FEATURE_COLUMN_ORDER",
    "AlignmentMetadata",
    "AgriculturalFeatures",
    "WeatherFeatures",
    "SatelliteFeatures",
    "SoilFeatures",
    "DerivedAgronomicFeatures",
    "MultiSourceObservation",
    "MultiSourceFeatureVector",
    "normalize_weather_response",
    "normalize_satellite_response",
    "normalize_soil_response",
    "normalize_agricultural_data",
    "FeatureEngineeringError",
    "SpatialAlignmentError",
    "TemporalAlignmentError",
    "DataLeakageError",
    "DataIntegrityError",
    "validate_coordinates",
    "validate_cross_source_spatial_alignment",
    "validate_satellite_date_window",
    "validate_temporal_alignment",
    "validate_no_target_leakage",
    "safe_ratio",
    "parse_iso_date",
    "MultiSourceFeatureBuilder",
    "feature_builder",
]
