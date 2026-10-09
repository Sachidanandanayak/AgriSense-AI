"""Pydantic schemas and request/response models for AgriSense AI."""

from app.schemas.weather import WeatherResponse
from app.schemas.satellite import SatelliteResponse, IndexStatistics
from app.schemas.soil import SoilResponse, SoilProperties
from app.services.feature_engineering.schemas import (
    MultiSourceObservation,
    MultiSourceFeatureVector,
    AlignmentMetadata,
    AgriculturalFeatures,
    WeatherFeatures,
    SatelliteFeatures,
    SoilFeatures,
    DerivedAgronomicFeatures,
    FEATURE_COLUMN_ORDER,
)

from app.schemas.recommendation import (
    AgriculturalInput,
    CropRecommendationItem,
    DataQualityReport,
    EnvironmentalContext,
    MANDATORY_DISCLAIMER,
    RecommendationRequest,
    RecommendationResponse,
)
from app.schemas.advisory import (
    ADVISORY_DISCLAIMER,
    CompatibilityStatus,
    CropAdvisoryItem,
    CropEnvironmentalRequirement,
    DataQualityAudit,
    FarmAdvisoryRequest,
    FarmAdvisoryResponse,
    RequirementProvenance,
    SatelliteEnvironmentalContext,
    VariableCompatibility,
    WaterAdvisory,
    WaterAdvisoryStatus,
)

__all__ = [
    "WeatherResponse",
    "SatelliteResponse",
    "IndexStatistics",
    "SoilResponse",
    "SoilProperties",
    "MultiSourceObservation",
    "MultiSourceFeatureVector",
    "AlignmentMetadata",
    "AgriculturalFeatures",
    "WeatherFeatures",
    "SatelliteFeatures",
    "SoilFeatures",
    "DerivedAgronomicFeatures",
    "FEATURE_COLUMN_ORDER",
    "AgriculturalInput",
    "CropRecommendationItem",
    "DataQualityReport",
    "EnvironmentalContext",
    "MANDATORY_DISCLAIMER",
    "RecommendationRequest",
    "RecommendationResponse",
    "ADVISORY_DISCLAIMER",
    "CompatibilityStatus",
    "CropAdvisoryItem",
    "CropEnvironmentalRequirement",
    "DataQualityAudit",
    "FarmAdvisoryRequest",
    "FarmAdvisoryResponse",
    "RequirementProvenance",
    "SatelliteEnvironmentalContext",
    "VariableCompatibility",
    "WaterAdvisory",
    "WaterAdvisoryStatus",
]

