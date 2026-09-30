"""Soil data service for AgriSense AI.

Orchestrates soil property lookups, input boundary validation, provider delegation,
and strict conversion from SoilGrids 2.0 mapped units into conventional agronomic units.
"""

from __future__ import annotations
import logging
from typing import Any

from app.schemas.soil import SoilProperties, SoilResponse
from app.services.soil_provider import (
    BaseSoilProvider,
    SoilGridsProvider,
    SOILGRIDS_PROPERTIES,
    SUPPORTED_DEPTH_INTERVALS,
    SoilProviderError,
    SoilProviderTimeoutError,
    SoilProviderConnectionError,
    SoilProviderRateLimitError,
    SoilProviderUnavailableError,
    MalformedSoilResponseError,
    NoSoilDataError,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Soil Exceptions
# ---------------------------------------------------------------------------


class SoilServiceError(Exception):
    """Base exception for all soil service errors."""


class InvalidCoordinatesError(SoilServiceError):
    """Raised when latitude or longitude coordinates fall outside valid physical bounds."""


class InvalidDepthError(SoilServiceError):
    """Raised when an unsupported depth interval is requested."""


# ---------------------------------------------------------------------------
# Coordinate and Depth Validation Helpers
# ---------------------------------------------------------------------------


def validate_coordinates(latitude: float, longitude: float) -> None:
    """Validate geographic coordinates within physical decimal degree limits.

    Args:
        latitude: Latitude between -90.0 and 90.0 degrees.
        longitude: Longitude between -180.0 and 180.0 degrees.

    Raises:
        InvalidCoordinatesError: If coordinates are out of bounds or non-numeric.
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


def validate_depth(depth_interval: str) -> str:
    """Validate requested depth interval against SoilGrids standard depths.

    Args:
        depth_interval: Depth interval string (e.g., '0-5cm').

    Returns:
        Cleaned depth interval string.

    Raises:
        InvalidDepthError: If depth interval is unsupported.
    """
    if not depth_interval or not isinstance(depth_interval, str):
        raise InvalidDepthError("Depth interval must be a non-empty string.")

    cleaned = depth_interval.strip().lower()
    if cleaned not in SUPPORTED_DEPTH_INTERVALS:
        supported_str = ", ".join(sorted(SUPPORTED_DEPTH_INTERVALS))
        raise InvalidDepthError(
            f"Unsupported depth interval '{depth_interval}'. Supported intervals: {supported_str}"
        )
    return cleaned


# ---------------------------------------------------------------------------
# Soil Service Implementation
# ---------------------------------------------------------------------------


class SoilService:
    """Service managing soil data retrieval, validation, and unit normalization."""

    def __init__(self, provider: BaseSoilProvider | None = None) -> None:
        self.provider: BaseSoilProvider = provider or SoilGridsProvider()

    def normalize_soil_data(
        self,
        raw_payload: dict[str, Any],
        latitude: float,
        longitude: float,
        depth_interval: str,
    ) -> SoilResponse:
        """Convert raw SoilGrids 2.0 GeoJSON layers into normalized SoilResponse schema.

        Applies explicit division by conversion factor (d_factor):
        - phh2o: mapped pH*10 / 10 -> pH
        - clay: mapped g/kg / 10 -> % (g/100g)
        - sand: mapped g/kg / 10 -> % (g/100g)
        - silt: mapped g/kg / 10 -> % (g/100g)
        - soc: mapped dg/kg / 10 -> g/kg
        - bdod: mapped cg/cm³ / 100 -> kg/dm³ (g/cm³)
        - cec: mapped mmol(c)/kg / 10 -> cmol(c)/kg
        - nitrogen: mapped cg/kg / 100 -> g/kg

        Args:
            raw_payload: Raw GeoJSON dictionary from SoilGrids.
            latitude: Queried latitude in decimal degrees.
            longitude: Queried longitude in decimal degrees.
            depth_interval: Queried depth interval.

        Returns:
            Normalized SoilResponse object.

        Raises:
            MalformedSoilResponseError: If payload structure is unexpected.
        """
        properties_block = raw_payload.get("properties")
        if not isinstance(properties_block, dict):
            raise MalformedSoilResponseError("Missing 'properties' block in SoilGrids response.")

        layers = properties_block.get("layers", [])
        if not isinstance(layers, list):
            raise MalformedSoilResponseError("'layers' in SoilGrids response is not a list.")

        # Index layers by name for O(1) lookup
        layer_dict: dict[str, Any] = {}
        for layer in layers:
            name = layer.get("name")
            if name:
                layer_dict[name] = layer

        # Extract and convert each property
        extracted_properties: dict[str, float | None] = {}

        for prop_name, prop_meta in SOILGRIDS_PROPERTIES.items():
            field_name = prop_meta["field_name"]
            d_factor = prop_meta["d_factor"]

            layer = layer_dict.get(prop_name)
            if not layer:
                extracted_properties[field_name] = None
                continue

            depths = layer.get("depths", [])
            if not depths or not isinstance(depths, list):
                extracted_properties[field_name] = None
                continue

            raw_mean = depths[0].get("values", {}).get("mean")
            if raw_mean is None:
                extracted_properties[field_name] = None
                continue

            try:
                converted_val = float(raw_mean) / float(d_factor)
                extracted_properties[field_name] = round(converted_val, 2)
            except (ValueError, TypeError, ZeroDivisionError) as exc:
                logger.warning(
                    "Error converting soil property %s (raw=%s): %s",
                    prop_name,
                    raw_mean,
                    exc,
                )
                extracted_properties[field_name] = None

        soil_properties = SoilProperties(**extracted_properties)

        return SoilResponse(
            latitude=round(float(latitude), 4),
            longitude=round(float(longitude), 4),
            depth_interval=depth_interval,
            soil=soil_properties,
            data_source="ISRIC SoilGrids 2.0",
            resolution_m=250,
        )

    async def get_soil_data(
        self,
        latitude: float,
        longitude: float,
        depth_interval: str = "0-5cm",
    ) -> SoilResponse:
        """Retrieve, validate, and normalize soil properties for coordinates and depth.

        Args:
            latitude: Target latitude in decimal degrees (-90 to 90).
            longitude: Target longitude in decimal degrees (-180 to 180).
            depth_interval: Standard depth interval (default '0-5cm').

        Returns:
            Normalized SoilResponse.

        Raises:
            InvalidCoordinatesError: On geographic coordinate boundary violations.
            InvalidDepthError: On unsupported depth interval.
            NoSoilDataError: When location has no soil data (e.g. water bodies).
            SoilProviderTimeoutError: On upstream timeout.
            SoilProviderRateLimitError: On rate limit exceeded.
            SoilProviderUnavailableError: On 5xx server outage.
            SoilProviderError: On unexpected provider errors.
        """
        validate_coordinates(latitude, longitude)
        validated_depth = validate_depth(depth_interval)

        raw_payload = await self.provider.fetch_soil_data(
            latitude=latitude,
            longitude=longitude,
            depth_interval=validated_depth,
        )

        return self.normalize_soil_data(
            raw_payload=raw_payload,
            latitude=latitude,
            longitude=longitude,
            depth_interval=validated_depth,
        )


# Singleton instance for route injection
soil_service = SoilService()
