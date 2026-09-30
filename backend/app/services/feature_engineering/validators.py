"""Validation utilities and custom exceptions for multi-source feature engineering.

Ensures spatial, temporal, and semantic alignment across heterogeneous agricultural,
meteorological, remote sensing, and soil data sources, preventing data leakage
and unscientific joins.
"""

from __future__ import annotations

from datetime import date, datetime
import math
from typing import Any


class FeatureEngineeringError(Exception):
    """Base exception for feature engineering failures."""


class SpatialAlignmentError(FeatureEngineeringError):
    """Raised when spatial coordinates fail validation or cross-source spatial alignment fails."""


class TemporalAlignmentError(FeatureEngineeringError):
    """Raised when dates are invalid or temporal alignment between observations fails."""


class DataLeakageError(FeatureEngineeringError):
    """Raised when supervised target labels or future observations leak into feature representations."""


class DataIntegrityError(FeatureEngineeringError):
    """Raised when data values violate domain boundaries or indicate fabricated inputs."""


def validate_coordinates(latitude: float, longitude: float) -> tuple[float, float]:
    """Validate geographic coordinates within standard WGS84 bounds.

    Args:
        latitude: Latitude in decimal degrees [-90.0, 90.0].
        longitude: Longitude in decimal degrees [-180.0, 180.0].

    Returns:
        Validated (latitude, longitude) tuple.

    Raises:
        SpatialAlignmentError: If coordinates are out of bounds or non-numeric.
    """
    if not isinstance(latitude, (int, float)) or math.isnan(latitude) or math.isinf(latitude):
        raise SpatialAlignmentError(f"Latitude must be a valid finite number, got {latitude}")

    if not isinstance(longitude, (int, float)) or math.isnan(longitude) or math.isinf(longitude):
        raise SpatialAlignmentError(f"Longitude must be a valid finite number, got {longitude}")

    if not (-90.0 <= latitude <= 90.0):
        raise SpatialAlignmentError(
            f"Latitude {latitude} out of valid range [-90.0, 90.0]"
        )

    if not (-180.0 <= longitude <= 180.0):
        raise SpatialAlignmentError(
            f"Longitude {longitude} out of valid range [-180.0, 180.0]"
        )

    return float(latitude), float(longitude)


from app.core.config import settings


def validate_cross_source_spatial_alignment(
    reference_lat: float,
    reference_lon: float,
    source_name: str,
    source_lat: float | None,
    source_lon: float | None,
    tolerance_deg: float | None = None,
) -> None:
    """Ensure coordinates from a secondary source align with the target location.

    NOTE: This tolerance is an engineering threshold to accommodate coordinate floating-point
    precision and provider grid-centroid snapping (~250m for SoilGrids, ~500m for Sentinel-2).
    It is NOT an agronomic boundary equivalence guarantee and does NOT claim cross-source
    observations within tolerance represent the exact same cadastral farm boundary.

    Args:
        reference_lat: Target observation latitude.
        reference_lon: Target observation longitude.
        source_name: Name of source being validated (e.g. 'Weather', 'Satellite', 'Soil').
        source_lat: Source latitude.
        source_lon: Source longitude.
        tolerance_deg: Maximum allowable difference in degrees (defaults to settings.FEATURE_SPATIAL_TOLERANCE_DEG).

    Raises:
        SpatialAlignmentError: If source coordinates differ beyond tolerance.
    """
    if source_lat is None or source_lon is None:
        return

    effective_tolerance = (
        tolerance_deg if tolerance_deg is not None else settings.FEATURE_SPATIAL_TOLERANCE_DEG
    )

    validate_coordinates(source_lat, source_lon)

    lat_diff = abs(reference_lat - source_lat)
    lon_diff = abs(reference_lon - source_lon)

    if lat_diff > effective_tolerance or lon_diff > effective_tolerance:
        raise SpatialAlignmentError(
            f"Spatial misalignment for {source_name}: source coordinates ({source_lat}, {source_lon}) "
            f"differ from target observation ({reference_lat}, {reference_lon}) "
            f"by ({lat_diff:.5f}°, {lon_diff:.5f}°), exceeding engineering tolerance {effective_tolerance}°."
        )


def parse_iso_date(value: str | date | datetime | None) -> date | None:
    """Parse date from ISO string, date, or datetime object.

    Args:
        value: String, date, datetime, or None.

    Returns:
        date object or None.

    Raises:
        TemporalAlignmentError: If string cannot be parsed as ISO date.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        # Handle full ISO timestamp (e.g., '2026-09-25T17:15')
        if "T" in cleaned:
            cleaned = cleaned.split("T")[0]
        try:
            return date.fromisoformat(cleaned)
        except ValueError as exc:
            raise TemporalAlignmentError(
                f"Invalid date format '{value}'. Expected ISO format YYYY-MM-DD: {exc}"
            ) from exc

    raise TemporalAlignmentError(f"Unsupported date type {type(value)}: {value}")


def validate_satellite_date_window(
    start_date: str | date,
    end_date: str | date,
) -> tuple[date, date]:
    """Validate satellite observation date window.

    Args:
        start_date: Window start date.
        end_date: Window end date.

    Returns:
        Tuple of (d_start, d_end) as date objects.

    Raises:
        TemporalAlignmentError: If start_date > end_date or dates are invalid.
    """
    d_start = parse_iso_date(start_date)
    d_end = parse_iso_date(end_date)

    if d_start is None or d_end is None:
        raise TemporalAlignmentError("Satellite start_date and end_date must both be provided.")

    if d_start > d_end:
        raise TemporalAlignmentError(
            f"Satellite start_date ({d_start}) cannot be after end_date ({d_end})."
        )

    return d_start, d_end


def validate_temporal_alignment(
    observation_date: str | date | None,
    satellite_start_date: str | date | None,
    satellite_end_date: str | date | None,
    weather_timestamp: str | None,
    satellite_max_window_days: int | None = None,
    max_weather_gap_days: int | None = None,
) -> None:
    """Verify temporal coherence between target observation date and data sources.

    NOTE: Temporal margins represent engineering policies for remote-sensing revisits
    (Sentinel-2 ~5-day orbital revisit) and short-term meteorological indexing. They are
    configurable engineering alignment parameters, NOT universal agronomic constants.

    Anti-Leakage Enforcement:
    Observations occurring in the future relative to the observation date are strictly
    rejected to prevent future information leakage into prediction-time feature sets.

    Args:
        observation_date: Intended target observation/planting date.
        satellite_start_date: Sentinel-2 window start.
        satellite_end_date: Sentinel-2 window end.
        weather_timestamp: Meteorological observation timestamp.
        satellite_max_window_days: Maximum allowable gap between satellite window end and observation date.
        max_weather_gap_days: Maximum allowable disparity between observation date and weather.

    Raises:
        TemporalAlignmentError: If temporal incoherence or forward data leakage is detected.
    """
    effective_sat_margin = (
        satellite_max_window_days
        if satellite_max_window_days is not None
        else settings.FEATURE_SATELLITE_MAX_WINDOW_DAYS
    )
    effective_weather_gap = (
        max_weather_gap_days
        if max_weather_gap_days is not None
        else settings.FEATURE_WEATHER_MAX_GAP_DAYS
    )

    obs_d = parse_iso_date(observation_date)
    if obs_d is None:
        # If observation_date is not specified, ensure satellite internal consistency
        if satellite_start_date and satellite_end_date:
            validate_satellite_date_window(satellite_start_date, satellite_end_date)
        return

    # Check satellite window relative to observation date
    if satellite_start_date and satellite_end_date:
        sat_start, sat_end = validate_satellite_date_window(
            satellite_start_date, satellite_end_date
        )

        # Anti-leakage: satellite_end_date MUST be <= observation_date for prediction-time features
        if sat_end > obs_d:
            raise TemporalAlignmentError(
                f"Future data leakage detected: Satellite observation window end ({sat_end}) "
                f"is after target observation date ({obs_d}). For prediction-time feature construction, "
                f"satellite imagery must end on or before the observation date."
            )

        # Stale window check: satellite composite window must end within allowable backward margin
        gap_past = (obs_d - sat_end).days
        if gap_past > effective_sat_margin:
            raise TemporalAlignmentError(
                f"Observation date ({obs_d}) is {gap_past} days after satellite observation window end "
                f"({sat_end}), exceeding allowable engineering margin of {effective_sat_margin} days."
            )

    # Check weather timestamp relative to observation date
    if weather_timestamp:
        weather_d = parse_iso_date(weather_timestamp)
        if weather_d:
            # Anti-leakage: weather observation date MUST be <= observation_date
            if weather_d > obs_d:
                raise TemporalAlignmentError(
                    f"Future data leakage detected: Weather observation date ({weather_d}) "
                    f"is after target observation date ({obs_d}). For prediction-time feature construction, "
                    f"weather observations cannot occur in the future."
                )

            # Stale weather check: weather observation must be within allowable backward gap
            gap_past = (obs_d - weather_d).days
            if gap_past > effective_weather_gap:
                raise TemporalAlignmentError(
                    f"Weather observation date ({weather_d}) is {gap_past} days prior to target "
                    f"observation date ({obs_d}), exceeding allowable engineering gap of {effective_weather_gap} days."
                )




def validate_no_target_leakage(feature_dict: dict[str, Any]) -> None:
    """Inspect feature dictionary to guarantee target labels are not present as input features.

    Args:
        feature_dict: Dictionary intended as ML prediction input.

    Raises:
        DataLeakageError: If target or target-derived keys are found.
    """
    forbidden_target_keys = {
        "crop_label",
        "label",
        "target",
        "target_crop_label",
        "crop",
        "predicted_crop",
        "actual_crop",
    }

    leaked = [k for k in feature_dict if k.lower() in forbidden_target_keys]
    if leaked:
        raise DataLeakageError(
            f"CRITICAL DATA LEAKAGE: Target variable(s) {leaked} detected in feature representation. "
            f"Supervised crop labels must remain strictly isolated as prediction targets."
        )


def safe_ratio(
    numerator: float | None,
    denominator: float | None,
    precision: int = 4,
) -> float | None:
    """Compute ratio safely with zero-denominator and null protection.

    Scientifically, nutrient and environmental ratios are undefined when denominator is zero,
    negative, or missing. This function returns None rather than generating synthetic zeros,
    infinities, or throwing unhandled division errors.

    Args:
        numerator: Numerator value.
        denominator: Denominator value.
        precision: Decimal rounding precision.

    Returns:
        Rounded float ratio or None if calculation is invalid.
    """
    if numerator is None or denominator is None:
        return None

    if not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
        return None

    if math.isnan(numerator) or math.isnan(denominator):
        return None

    # Zero or negative denominator cannot form a valid agronomic ratio
    if denominator <= 0.0:
        return None

    # Negative numerator is agronomic nonsense for chemical/physical contents
    if numerator < 0.0:
        return None

    ratio = numerator / denominator
    return round(float(ratio), precision)
