"""Custom exceptions for Crop Suitability & Recommendation Engine."""

from __future__ import annotations


class RecommendationError(Exception):
    """Base exception for all recommendation service errors."""


class RecommendationValidationError(RecommendationError):
    """Raised when request validation fails (coordinates, dates, ranges)."""


class InvalidCoordinatesError(RecommendationValidationError):
    """Raised when latitude or longitude falls outside geographic bounds."""


class InvalidDateError(RecommendationValidationError):
    """Raised when observation date format or range is invalid."""


class MissingModelInputError(RecommendationValidationError):
    """Raised when required benchmark model features are missing or None.
    
    Silent imputation of missing critical inputs is strictly prohibited.
    """


class IncompatibleFeatureSchemaError(RecommendationError):
    """Raised when input feature dictionary does not match expected model schema."""


class ModelUnavailableError(RecommendationError):
    """Raised when trained model artifact is not found or cannot be loaded."""


class ModelPredictionError(RecommendationError):
    """Raised when model inference execution fails."""
