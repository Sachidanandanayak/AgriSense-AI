"""Custom domain exceptions for Farm Advisory Engine."""

from __future__ import annotations


class FarmAdvisoryError(Exception):
    """Base exception for all farm advisory domain errors."""


class InvalidAdvisoryRequestError(FarmAdvisoryError):
    """Raised when an advisory request fails validation."""


class CropRequirementNotFoundError(FarmAdvisoryError):
    """Raised when authoritative requirement profile is not found for a crop."""


class AdvisoryDataAlignmentError(FarmAdvisoryError):
    """Raised when multi-source environmental data cannot be aligned."""


class WaterAdvisoryCalculationError(FarmAdvisoryError):
    """Raised when defensible water-related calculations fail."""


class AdvisoryServiceUnavailableError(FarmAdvisoryError):
    """Raised when an underlying dependency or service is unavailable."""
