"""Soil data provider interface and ISRIC SoilGrids 2.0 implementation for AgriSense AI.

Encapsulates upstream HTTP interactions, network resiliency, fair-use adherence,
and raw GeoJSON layer extraction while isolating provider-specific schema details.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Soil Provider Exceptions
# ---------------------------------------------------------------------------


class SoilProviderError(Exception):
    """Base exception for all soil provider errors."""


class SoilProviderTimeoutError(SoilProviderError):
    """Raised when an external soil provider request exceeds the timeout threshold."""


class SoilProviderConnectionError(SoilProviderError):
    """Raised when network connectivity to the soil provider fails."""


class SoilProviderRateLimitError(SoilProviderError):
    """Raised when external soil provider rate limits are exceeded."""


class SoilProviderUnavailableError(SoilProviderError):
    """Raised when the soil provider returns 5xx or is temporarily down."""


class MalformedSoilResponseError(SoilProviderError):
    """Raised when the provider response cannot be parsed or lacks expected structure."""


class NoSoilDataError(SoilProviderError):
    """Raised when the requested location falls outside soil coverage (e.g., water, urban, unmodeled)."""


# ---------------------------------------------------------------------------
# SoilGrids 2.0 Property Definitions & Documented Conversion Factors
# ---------------------------------------------------------------------------

SOILGRIDS_PROPERTIES: dict[str, dict[str, Any]] = {
    "phh2o": {
        "field_name": "ph",
        "mapped_unit": "pH*10",
        "target_unit": "pH",
        "d_factor": 10,
        "description": "Soil pH in H2O",
    },
    "clay": {
        "field_name": "clay_pct",
        "mapped_unit": "g/kg",
        "target_unit": "%",
        "d_factor": 10,
        "description": "Clay content (0-2 um)",
    },
    "sand": {
        "field_name": "sand_pct",
        "mapped_unit": "g/kg",
        "target_unit": "%",
        "d_factor": 10,
        "description": "Sand content (50-2000 um)",
    },
    "silt": {
        "field_name": "silt_pct",
        "mapped_unit": "g/kg",
        "target_unit": "%",
        "d_factor": 10,
        "description": "Silt content (2-50 um)",
    },
    "soc": {
        "field_name": "organic_carbon_g_kg",
        "mapped_unit": "dg/kg",
        "target_unit": "g/kg",
        "d_factor": 10,
        "description": "Soil organic carbon",
    },
    "bdod": {
        "field_name": "bulk_density",
        "mapped_unit": "cg/cm³",
        "target_unit": "kg/dm³",
        "d_factor": 100,
        "description": "Bulk density of fine earth fraction",
    },
    "cec": {
        "field_name": "cec",
        "mapped_unit": "mmol(c)/kg",
        "target_unit": "cmol(c)/kg",
        "d_factor": 10,
        "description": "Cation exchange capacity at pH 7",
    },
    "nitrogen": {
        "field_name": "nitrogen_g_kg",
        "mapped_unit": "cg/kg",
        "target_unit": "g/kg",
        "d_factor": 100,
        "description": "Total nitrogen",
    },
}

SUPPORTED_DEPTH_INTERVALS: set[str] = {
    "0-5cm",
    "5-15cm",
    "15-30cm",
    "30-60cm",
    "60-100cm",
    "100-200cm",
}


# ---------------------------------------------------------------------------
# Abstract Base Soil Provider
# ---------------------------------------------------------------------------


class BaseSoilProvider(ABC):
    """Abstract interface defining required behavior for digital soil map providers."""

    @abstractmethod
    async def fetch_soil_data(
        self,
        latitude: float,
        longitude: float,
        depth_interval: str = "0-5cm",
    ) -> dict[str, Any]:
        """Fetch raw soil property layers from the provider.

        Args:
            latitude: Target latitude in decimal degrees (-90 to 90).
            longitude: Target longitude in decimal degrees (-180 to 180).
            depth_interval: Standard depth interval (default 0-5cm).

        Returns:
            Provider-specific raw data structure.

        Raises:
            SoilProviderError: On upstream communication or parsing failure.
        """


# ---------------------------------------------------------------------------
# ISRIC SoilGrids 2.0 Concrete Provider
# ---------------------------------------------------------------------------


class SoilGridsProvider(BaseSoilProvider):
    """ISRIC SoilGrids 2.0 REST API client.

    Documentation: https://docs.isric.org/globaldata/soilgrids/
    Beta Service Notice: SoilGrids v2.0 REST API is a beta service provided without
    strict availability SLAs. This client encapsulates timeouts, retries, and fair-use
    adherence (up to 5 calls/min recommended by ISRIC).
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url or settings.SOILGRIDS_BASE_URL
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.SOILGRIDS_TIMEOUT_SECONDS
        )
        self._external_client = client

    async def fetch_soil_data(
        self,
        latitude: float,
        longitude: float,
        depth_interval: str = "0-5cm",
    ) -> dict[str, Any]:
        """Query SoilGrids 2.0 REST API for point coordinates and depth interval.

        Args:
            latitude: Latitude coordinate (-90 to 90).
            longitude: Longitude coordinate (-180 to 180).
            depth_interval: Target depth interval.

        Returns:
            Raw GeoJSON dictionary parsed from SoilGrids response.

        Raises:
            SoilProviderTimeoutError: If the upstream request times out.
            SoilProviderConnectionError: If network connection fails.
            SoilProviderRateLimitError: If HTTP 429 is encountered.
            SoilProviderUnavailableError: If HTTP 5xx or server outage occurs.
            SoilProviderError: On non-200 HTTP status.
            MalformedSoilResponseError: If JSON structure is corrupt or unparseable.
            NoSoilDataError: If all property layers return null (unmodeled mask).
        """
        # Build query parameters according to SoilGrids v2.0 OpenAPI spec
        # Passing multiple property params requests only relevant agricultural layers
        query_params: list[tuple[str, str]] = [
            ("lat", str(latitude)),
            ("lon", str(longitude)),
            ("depth", depth_interval),
            ("value", "mean"),
        ]
        for prop in SOILGRIDS_PROPERTIES.keys():
            query_params.append(("property", prop))

        headers = {
            "Accept": "application/json",
            "User-Agent": "AgriSense-AI/0.1.0 (Farm-Advisory-Platform; research)",
        }

        try:
            if self._external_client:
                response = await self._external_client.get(
                    self.base_url,
                    params=query_params,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        self.base_url,
                        params=query_params,
                        headers=headers,
                        timeout=self.timeout_seconds,
                    )
        except httpx.TimeoutException as exc:
            logger.error("SoilGrids provider request timed out: %s", exc)
            raise SoilProviderTimeoutError(
                f"SoilGrids request timed out after {self.timeout_seconds}s."
            ) from exc
        except httpx.NetworkError as exc:
            logger.error("SoilGrids provider network connection failed: %s", exc)
            raise SoilProviderConnectionError(
                f"Failed to connect to SoilGrids service: {exc}"
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected error contacting SoilGrids: %s", exc)
            raise SoilProviderError(f"Unexpected error querying SoilGrids: {exc}") from exc

        # Handle HTTP status codes
        if response.status_code == 429:
            logger.warning("SoilGrids rate limit exceeded (HTTP 429).")
            raise SoilProviderRateLimitError(
                "SoilGrids API rate limit exceeded. Please retry later adhering to fair use."
            )
        if response.status_code in (500, 502, 503, 504):
            logger.error(
                "SoilGrids returned server error %d: %s",
                response.status_code,
                response.text[:200],
            )
            raise SoilProviderUnavailableError(
                f"SoilGrids upstream server error (HTTP {response.status_code})."
            )
        if response.status_code != 200:
            logger.error(
                "SoilGrids returned unexpected status %d: %s",
                response.status_code,
                response.text[:200],
            )
            raise SoilProviderError(
                f"SoilGrids returned unexpected HTTP status {response.status_code}."
            )

        # Parse JSON
        try:
            payload = response.json()
        except Exception as exc:
            logger.error("Failed to parse SoilGrids JSON: %s", exc)
            raise MalformedSoilResponseError(
                "SoilGrids returned malformed or unparseable JSON response."
            ) from exc

        if not isinstance(payload, dict):
            raise MalformedSoilResponseError("SoilGrids payload is not a valid JSON object.")

        # Check layers existence
        properties_block = payload.get("properties")
        if not isinstance(properties_block, dict):
            raise MalformedSoilResponseError("SoilGrids response lacks 'properties' object.")

        layers = properties_block.get("layers")
        if not isinstance(layers, list) or len(layers) == 0:
            raise NoSoilDataError(
                "No soil layers found in SoilGrids response for requested coordinates."
            )

        # Check if all returned layers have null mean values (e.g. water bodies, urban masks)
        all_null = True
        for layer in layers:
            depths = layer.get("depths", [])
            if depths and isinstance(depths, list):
                val = depths[0].get("values", {}).get("mean")
                if val is not None:
                    all_null = False
                    break

        if all_null:
            raise NoSoilDataError(
                "No soil data available from SoilGrids for the requested coordinates "
                "(location may be a water body, unmodeled area, or outside coverage)."
            )

        return payload
