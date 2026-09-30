"""Input validators and boundary checks for recommendation engine."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.services.recommendation.exceptions import (
    InvalidCoordinatesError,
    InvalidDateError,
    MissingModelInputError,
    RecommendationValidationError,
)
from app.services.recommendation.schemas import AgriculturalInput


def validate_coordinates(latitude: Any, longitude: Any) -> tuple[float, float]:
    """Validate geographic coordinates within physical WGS84 bounds.

    Args:
        latitude: Latitude in decimal degrees (-90.0 to 90.0).
        longitude: Longitude in decimal degrees (-180.0 to 180.0).

    Returns:
        Tuple of validated (latitude, longitude) as floats rounded to 4 decimals.

    Raises:
        InvalidCoordinatesError: If coordinates are non-numeric or out of bounds.
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (ValueError, TypeError) as exc:
        raise InvalidCoordinatesError(
            f"Coordinates must be valid numbers: latitude={latitude}, longitude={longitude}"
        ) from exc

    if not (-90.0 <= lat <= 90.0):
        raise InvalidCoordinatesError(
            f"Invalid latitude {lat}. Latitude must be between -90.0 and 90.0 degrees."
        )

    if not (-180.0 <= lon <= 180.0):
        raise InvalidCoordinatesError(
            f"Invalid longitude {lon}. Longitude must be between -180.0 and 180.0 degrees."
        )

    return round(lat, 4), round(lon, 4)


def validate_observation_date(date_val: str | date | None) -> str | None:
    """Validate observation date format (YYYY-MM-DD).

    Args:
        date_val: Date object or ISO date string.

    Returns:
        Standardized ISO date string YYYY-MM-DD or None.

    Raises:
        InvalidDateError: If date cannot be parsed or format is invalid.
    """
    if date_val is None:
        return None

    if isinstance(date_val, date):
        return date_val.isoformat()

    if isinstance(date_val, str):
        cleaned = date_val.strip()
        if not cleaned:
            return None
        try:
            parsed = datetime.strptime(cleaned, "%Y-%m-%d").date()
            return parsed.isoformat()
        except ValueError as exc:
            raise InvalidDateError(
                f"Invalid date format '{date_val}'. Expected ISO format YYYY-MM-DD."
            ) from exc

    raise InvalidDateError(f"Unsupported date type: {type(date_val)}")


def validate_agricultural_inputs(inputs: AgriculturalInput | None) -> AgriculturalInput:
    """Validate that required agricultural model inputs are provided and complete.

    The benchmark Random Forest model requires 7 baseline features:
    N, P, K, temperature, humidity, pH, rainfall. Silent imputation is prohibited.

    Args:
        inputs: AgriculturalInput instance or None.

    Returns:
        Validated AgriculturalInput instance.

    Raises:
        MissingModelInputError: If inputs is None or any required field is missing/None.
    """
    if inputs is None:
        raise MissingModelInputError(
            "Missing required agricultural inputs. The benchmark model requires "
            "'nitrogen', 'phosphorus', 'potassium', 'temperature', 'humidity', "
            "'ph', and 'rainfall'. Silent imputation is strictly prohibited."
        )

    required_fields = [
        "nitrogen",
        "phosphorus",
        "potassium",
        "temperature",
        "humidity",
        "ph",
        "rainfall",
    ]
    missing = [f for f in required_fields if getattr(inputs, f, None) is None]

    if missing:
        raise MissingModelInputError(
            f"Missing required model input features: {missing}. "
            "Silent imputation of missing critical inputs is strictly prohibited."
        )

    return inputs


def validate_top_k(top_k: int, max_classes: int = 22) -> int:
    """Validate top_k recommendations count.

    Args:
        top_k: Number of recommendations requested.
        max_classes: Total number of classes recognized by model (22).

    Returns:
        Validated integer top_k.

    Raises:
        RecommendationValidationError: If top_k is less than 1 or exceeds max_classes.
    """
    try:
        k = int(top_k)
    except (ValueError, TypeError) as exc:
        raise RecommendationValidationError(
            f"top_k must be an integer, got: {top_k}"
        ) from exc

    if not (1 <= k <= max_classes):
        raise RecommendationValidationError(
            f"top_k must be between 1 and {max_classes}, got {k}."
        )

    return k
