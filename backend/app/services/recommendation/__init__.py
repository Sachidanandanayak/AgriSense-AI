"""Crop Suitability & Recommendation Service package for AgriSense AI."""

from app.services.recommendation.exceptions import (
    IncompatibleFeatureSchemaError,
    InvalidCoordinatesError,
    InvalidDateError,
    MissingModelInputError,
    ModelPredictionError,
    ModelUnavailableError,
    RecommendationError,
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
    DataQualityReport,
    EnvironmentalContext,
    MANDATORY_DISCLAIMER,
    RecommendationRequest,
    RecommendationResponse,
)

__all__ = [
    "AgriculturalInput",
    "CropModelAdapter",
    "CropRecommendationItem",
    "DataQualityReport",
    "EXPECTED_MODEL_FEATURES",
    "EnvironmentalContext",
    "IncompatibleFeatureSchemaError",
    "InvalidCoordinatesError",
    "InvalidDateError",
    "MANDATORY_DISCLAIMER",
    "MissingModelInputError",
    "ModelPredictionError",
    "ModelUnavailableError",
    "RecommendationError",
    "RecommendationRequest",
    "RecommendationResponse",
    "RecommendationService",
    "RecommendationValidationError",
    "crop_model_adapter",
    "generate_explanations",
    "generate_limitations",
    "recommendation_service",
]
