"""Validation and data freshness auditing for Farm Advisory Engine."""

from __future__ import annotations

from datetime import date, datetime
import logging
from typing import Tuple

from app.core.config import settings
from app.schemas.satellite import SatelliteResponse
from app.schemas.weather import WeatherResponse
from app.services.farm_advisory.exceptions import InvalidAdvisoryRequestError

logger = logging.getLogger(__name__)


def validate_advisory_coordinates(latitude: float, longitude: float) -> Tuple[float, float]:
    """Validate spatial coordinate boundaries for advisory analysis."""
    if not isinstance(latitude, (int, float)) or not (-90.0 <= float(latitude) <= 90.0):
        raise InvalidAdvisoryRequestError(
            f"Latitude {latitude} is outside valid WGS84 bounds [-90.0, 90.0]."
        )
    if not isinstance(longitude, (int, float)) or not (-180.0 <= float(longitude) <= 180.0):
        raise InvalidAdvisoryRequestError(
            f"Longitude {longitude} is outside valid WGS84 bounds [-180.0, 180.0]."
        )
    return round(float(latitude), 4), round(float(longitude), 4)


def validate_advisory_date(observation_date: str | None) -> str | None:
    """Validate ISO date format YYYY-MM-DD."""
    if observation_date is None:
        return None
    try:
        parsed = datetime.strptime(observation_date, "%Y-%m-%d").date()
        return parsed.isoformat()
    except ValueError as exc:
        raise InvalidAdvisoryRequestError(
            f"Invalid observation date format '{observation_date}'. Expected ISO format YYYY-MM-DD."
        ) from exc


def audit_data_freshness(
    weather: WeatherResponse | None,
    satellite: SatelliteResponse | None,
    target_date_str: str | None,
) -> Tuple[list[str], list[str]]:
    """Audit temporal freshness of attached environmental data.

    Returns:
        Tuple of (stale_sources, staleness_warnings).
    """
    stale_sources: list[str] = []
    warnings: list[str] = []

    ref_date = (
        datetime.strptime(target_date_str, "%Y-%m-%d").date()
        if target_date_str
        else date.today()
    )

    # 1. Audit weather freshness
    if weather is not None and weather.weather_timestamp:
        try:
            # Parse ISO timestamp (e.g. '2026-09-25T17:15' or with seconds/timezone)
            cleaned = weather.weather_timestamp.replace("Z", "+00:00")
            weather_dt = datetime.fromisoformat(cleaned).date()
            gap_days = abs((ref_date - weather_dt).days)
            if gap_days > settings.FEATURE_WEATHER_MAX_GAP_DAYS:
                stale_sources.append("weather")
                warnings.append(
                    f"Weather observation timestamp ({weather.weather_timestamp}) is {gap_days} days "
                    f"apart from target date ({ref_date.isoformat()}), exceeding max freshness gap ({settings.FEATURE_WEATHER_MAX_GAP_DAYS} days)."
                )
        except Exception as exc:
            logger.debug("Could not parse weather timestamp for freshness audit: %s", exc)

    # 2. Audit satellite freshness
    if satellite is not None and satellite.end_date:
        try:
            sat_end_dt = datetime.strptime(satellite.end_date, "%Y-%m-%d").date()
            gap_days = abs((ref_date - sat_end_dt).days)
            if gap_days > settings.FEATURE_SATELLITE_MAX_WINDOW_DAYS:
                stale_sources.append("satellite")
                warnings.append(
                    f"Satellite composite window end date ({satellite.end_date}) is {gap_days} days "
                    f"apart from target date ({ref_date.isoformat()}), exceeding freshness window ({settings.FEATURE_SATELLITE_MAX_WINDOW_DAYS} days)."
                )
        except Exception as exc:
            logger.debug("Could not parse satellite end_date for freshness audit: %s", exc)

    return stale_sources, warnings
