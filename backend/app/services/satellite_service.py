"""Satellite data integration service for AgriSense AI.

Interfaces with Google Earth Engine to query Sentinel-2 Harmonized Surface Reflectance
imagery, applies pixel-level cloud probability filtering, generates temporal median
composites, computes key agricultural vegetation/moisture indices (NDVI, NDWI, NDMI),
and calculates zonal regional statistics for localized farm coordinates.
"""

from __future__ import annotations
import asyncio
from datetime import date, datetime, timedelta
import logging
import math
from typing import Any

from app.core.config import settings
from app.schemas.satellite import SatelliteResponse, IndexStatistics

logger = logging.getLogger(__name__)

# Lazy or safe import of Earth Engine
try:
    import ee
except ImportError:  # pragma: no cover
    ee = None  # type: ignore


# ---------------------------------------------------------------------------
# Custom Satellite Exceptions
# ---------------------------------------------------------------------------


class SatelliteServiceError(Exception):
    """Base exception for all satellite service errors."""


class InvalidCoordinatesError(SatelliteServiceError):
    """Raised when latitude or longitude coordinates fall outside valid geographic bounds."""


class InvalidDateRangeError(SatelliteServiceError):
    """Raised when query start_date or end_date are invalid or incorrectly ordered."""


class InvalidParameterError(SatelliteServiceError):
    """Raised when query parameters (radius, cloud threshold) fall outside permitted bounds."""


class EarthEngineAuthError(SatelliteServiceError):
    """Raised when Earth Engine authentication is unconfigured, expired, or invalid."""


class EarthEngineInitError(SatelliteServiceError):
    """Raised when Earth Engine fails to initialize or connect to Google Cloud."""


class NoObservationsFoundError(SatelliteServiceError):
    """Raised when no suitable cloud-free Sentinel-2 observations exist for the query."""


class EarthEngineExecutionError(SatelliteServiceError):
    """Raised when an Earth Engine computation, query, or reduction fails."""


# ---------------------------------------------------------------------------
# Pure Deterministic Spectral Index Calculation Helpers
# ---------------------------------------------------------------------------


def compute_ndvi(nir: float, red: float) -> float:
    """Calculate Normalized Difference Vegetation Index (NDVI).

    Formula: (B8 - B4) / (B8 + B4)
    Reflectance inputs: Near-Infrared (B8, ~842nm) and Red (B4, ~665nm).
    Measures green canopy vigor and biomass density.
    Safely handles zero or near-zero denominators.

    Args:
        nir: Near-Infrared reflectance value (Band 8).
        red: Red reflectance value (Band 4).

    Returns:
        NDVI value clamped between -1.0 and 1.0.
    """
    denom = nir + red
    if abs(denom) < 1e-7:
        return 0.0
    val = (nir - red) / denom
    if math.isnan(val) or math.isinf(val):
        return 0.0
    return float(max(-1.0, min(1.0, val)))


def compute_ndwi(green: float, nir: float) -> float:
    """Calculate Normalized Difference Water Index (NDWI) - McFeeters (1996).

    Formula: (B3 - B8) / (B3 + B8)
    Reflectance inputs: Green (B3, ~560nm) and Near-Infrared (B8, ~842nm).

    *Definition Note*:
    AgriSense AI strictly adopts the McFeeters (1996) formulation for NDWI to
    delineate open surface water, localized ponding, drainage issues, and soil
    inundation. Open water exhibits positive values (> 0.0), whereas vegetation
    and terrestrial soil yield negative values. (For plant canopy moisture,
    refer to NDMI / Gao 1996).

    Args:
        green: Green reflectance value (Band 3).
        nir: Near-Infrared reflectance value (Band 8).

    Returns:
        NDWI value clamped between -1.0 and 1.0.
    """
    denom = green + nir
    if abs(denom) < 1e-7:
        return 0.0
    val = (green - nir) / denom
    if math.isnan(val) or math.isinf(val):
        return 0.0
    return float(max(-1.0, min(1.0, val)))


def compute_ndmi(nir: float, swir: float) -> float:
    """Calculate Normalized Difference Moisture Index (NDMI) - Gao (1996).

    Formula: (B8 - B11) / (B8 + B11)
    Reflectance inputs: Near-Infrared (B8, ~842nm) and Short-Wave Infrared (B11, ~1610nm).

    *Definition Note*:
    Also referred to in scientific literature as NDWI_Gao (Gao 1996). In AgriSense AI,
    we term this NDMI to prevent naming collisions with McFeeters' water index.
    NDMI measures liquid water content within plant canopies and internal leaf
    structure. Higher values signify well-hydrated vegetation; declining or
    negative values indicate water stress or moisture deficit.

    Args:
        nir: Near-Infrared reflectance value (Band 8).
        swir: Short-Wave Infrared reflectance value (Band 11).

    Returns:
        NDMI value clamped between -1.0 and 1.0.
    """
    denom = nir + swir
    if abs(denom) < 1e-7:
        return 0.0
    val = (nir - swir) / denom
    if math.isnan(val) or math.isinf(val):
        return 0.0
    return float(max(-1.0, min(1.0, val)))


# ---------------------------------------------------------------------------
# Validation Helpers
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


def validate_date_range(start_date: str, end_date: str) -> tuple[date, date]:
    """Validate date strings and ordering.

    Args:
        start_date: ISO date string (YYYY-MM-DD).
        end_date: ISO date string (YYYY-MM-DD).

    Returns:
        Tuple of parsed (start_date, end_date) date objects.

    Raises:
        InvalidDateRangeError: If dates are malformed or start_date > end_date.
    """
    try:
        d_start = datetime.strptime(start_date, "%Y-%m-%d").date()
    except (ValueError, TypeError) as exc:
        raise InvalidDateRangeError(
            f"Invalid start_date '{start_date}'. Must be in YYYY-MM-DD format."
        ) from exc

    try:
        d_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except (ValueError, TypeError) as exc:
        raise InvalidDateRangeError(
            f"Invalid end_date '{end_date}'. Must be in YYYY-MM-DD format."
        ) from exc

    if d_start > d_end:
        raise InvalidDateRangeError(
            f"start_date ({start_date}) must be less than or equal to end_date ({end_date})."
        )

    return d_start, d_end


def validate_parameters(
    radius_m: float,
    cloud_probability_threshold: float,
) -> None:
    """Validate numeric parameters for radius and cloud threshold.

    Args:
        radius_m: Radius around point coordinate in meters (10 to 50000).
        cloud_probability_threshold: Cloud cutoff percentage (0 to 100).

    Raises:
        InvalidParameterError: If values are out of allowable ranges.
    """
    if radius_m <= 0.0 or radius_m > 50000.0:
        raise InvalidParameterError(
            f"Invalid radius_m ({radius_m}). Must be a positive number between 10 and 50,000 meters."
        )
    if not (0.0 <= cloud_probability_threshold <= 100.0):
        raise InvalidParameterError(
            f"Invalid cloud_probability_threshold ({cloud_probability_threshold}). "
            "Must be between 0.0 and 100.0 percent."
        )


# ---------------------------------------------------------------------------
# Satellite Service Class
# ---------------------------------------------------------------------------


class SatelliteService:
    """Service encapsulating Google Earth Engine integration for Sentinel-2 indices."""

    def __init__(
        self,
        project_id: str | None = None,
        service_account: str | None = None,
        key_file: str | None = None,
        private_key: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.project_id = project_id or settings.EARTHENGINE_PROJECT
        self.service_account = service_account or settings.EARTHENGINE_SERVICE_ACCOUNT
        self.key_file = key_file or settings.EARTHENGINE_KEY_FILE
        self.private_key = private_key or settings.EARTHENGINE_PRIVATE_KEY
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.EARTHENGINE_TIMEOUT_SECONDS
        )
        self._ee_initialized = False

    def initialize_earth_engine(self) -> None:
        """Initialize Google Earth Engine API using configured credentials.

        Raises:
            EarthEngineAuthError: If authentication credentials are missing or invalid.
            EarthEngineInitError: If connection to Earth Engine fails.
        """
        if self._ee_initialized:
            return

        if ee is None:
            raise EarthEngineInitError(
                "earthengine-api package is not installed. Please install earthengine-api."
            )

        try:
            # 1. Service account authentication (headless / CI / automated production)
            if self.service_account and (self.key_file or self.private_key):
                logger.info(
                    "Initializing Earth Engine with service account: %s",
                    self.service_account,
                )
                key_data = self.key_file or self.private_key
                credentials = ee.ServiceAccountCredentials(
                    self.service_account, key_data
                )
                ee.Initialize(
                    credentials=credentials,
                    project=self.project_id,
                )
            # 2. Standard user OAuth / ADC initialization (local development)
            elif self.project_id:
                logger.info(
                    "Initializing Earth Engine with project: %s", self.project_id
                )
                ee.Initialize(project=self.project_id)
            else:
                # Attempt default initialization if credentials exist in user config
                logger.info("Initializing Earth Engine with default user credentials")
                ee.Initialize()

            self._ee_initialized = True
            logger.info("Google Earth Engine initialized successfully.")

        except Exception as exc:
            err_msg = str(exc)
            logger.warning("Earth Engine initialization failed: %s", err_msg)
            if "authorize access" in err_msg.lower() or "credentials" in err_msg.lower() or "project" in err_msg.lower():
                raise EarthEngineAuthError(
                    "Google Earth Engine is not authenticated. Please configure EARTHENGINE_PROJECT "
                    "or run 'earthengine authenticate' for local development."
                ) from exc
            raise EarthEngineInitError(
                f"Failed to initialize Earth Engine: {err_msg}"
            ) from exc

    def _execute_earth_engine_pipeline(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        radius_m: float,
        cloud_probability_threshold: float,
    ) -> dict[str, Any]:
        """Execute Earth Engine queries, masking, compositing, and zonal reduction.

        Args:
            latitude: Target latitude in decimal degrees.
            longitude: Target longitude in decimal degrees.
            start_date: Observation window start (YYYY-MM-DD).
            end_date: Observation window end (YYYY-MM-DD).
            radius_m: Circular analysis radius in meters.
            cloud_probability_threshold: Max cloud probability percentage.

        Returns:
            Dictionary containing usable_observations and index reduction statistics.
        """
        # Ensure Earth Engine is initialized
        self.initialize_earth_engine()

        # Build analysis geometry (circular buffer around farmer coordinate)
        point = ee.Geometry.Point([longitude, latitude])
        roi = point.buffer(radius_m)

        # In Earth Engine, filterDate end is exclusive; add 1 day so end_date is inclusive
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() + timedelta(days=1)
        end_date_inclusive = end_dt.strftime("%Y-%m-%d")

        # Sentinel-2 Harmonized Surface Reflectance & Cloud Probability Collections
        s2_sr = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(roi)
            .filterDate(start_date, end_date_inclusive)
        )

        s2_cloud = (
            ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
            .filterBounds(roi)
            .filterDate(start_date, end_date_inclusive)
        )

        # Join the two collections matching on system:index
        join_filter = ee.Filter.equals(
            leftField="system:index", rightField="system:index"
        )
        save_first_join = ee.Join.saveFirst(matchKey="cloud_mask")
        joined_collection = save_first_join.apply(
            primary=s2_sr, secondary=s2_cloud, condition=join_filter
        )

        # Retrieve count of usable scenes intersecting the ROI
        try:
            usable_count = int(joined_collection.size().getInfo())
        except Exception as exc:
            raise EarthEngineExecutionError(
                f"Failed to query Sentinel-2 observation count: {exc}"
            ) from exc

        if usable_count == 0:
            raise NoObservationsFoundError(
                "No suitable cloud-free Sentinel-2 observation was found for the requested location and date range."
            )

        # Pixel-level cloud probability masking function
        def mask_clouds(img: Any) -> Any:
            cloud_img = ee.Image(img.get("cloud_mask"))
            prob = cloud_img.select("probability")
            is_clear = prob.lt(cloud_probability_threshold)
            return img.updateMask(is_clear)

        cloud_masked_collection = ee.ImageCollection(joined_collection).map(mask_clouds)

        # Temporal Composite: Median composite across all cloud-cleared observations
        composite = cloud_masked_collection.median()

        # Compute Spectral Indices:
        # 1. NDVI: (B8 - B4) / (B8 + B4)
        ndvi = composite.normalizedDifference(["B8", "B4"]).rename("ndvi")
        # 2. NDWI (McFeeters 1996): (B3 - B8) / (B3 + B8)
        ndwi = composite.normalizedDifference(["B3", "B8"]).rename("ndwi")
        # 3. NDMI (Gao 1996): (B8 - B11) / (B8 + B11)
        ndmi = composite.normalizedDifference(["B8", "B11"]).rename("ndmi")

        indices_image = composite.addBands([ndvi, ndwi, ndmi]).select(
            ["ndvi", "ndwi", "ndmi"]
        )

        # Spatial Aggregation: Calculate robust zonal statistics over circular analysis region
        combined_reducer = (
            ee.Reducer.median()
            .setOutputs(["median"])
            .combine(ee.Reducer.mean().setOutputs(["mean"]), sharedInputs=True)
            .combine(ee.Reducer.min().setOutputs(["min"]), sharedInputs=True)
            .combine(ee.Reducer.max().setOutputs(["max"]), sharedInputs=True)
            .combine(ee.Reducer.stdDev().setOutputs(["stdDev"]), sharedInputs=True)
        )

        try:
            stats = indices_image.reduceRegion(
                reducer=combined_reducer,
                geometry=roi,
                scale=10,  # Sentinel-2 10m native ground sampling distance
                maxPixels=1e8,
                bestEffort=True,
            ).getInfo()
        except Exception as exc:
            raise EarthEngineExecutionError(
                f"Failed to aggregate satellite indices over region: {exc}"
            ) from exc

        # If all pixels were cloudy or unmasked within the buffer, median will be None
        if not stats or stats.get("ndvi_median") is None:
            raise NoObservationsFoundError(
                "No suitable cloud-free Sentinel-2 observation was found for the requested location and date range."
            )

        return {
            "usable_observations": usable_count,
            "stats": stats,
        }

    async def get_satellite_data(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        radius_m: float = 500.0,
        cloud_probability_threshold: float = 65.0,
    ) -> SatelliteResponse:
        """Fetch, cloud-filter, composite, and calculate Sentinel-2 indices.

        Args:
            latitude: Latitude coordinate in decimal degrees (-90 to 90).
            longitude: Longitude coordinate in decimal degrees (-180 to 180).
            start_date: ISO start date string (YYYY-MM-DD).
            end_date: ISO end date string (YYYY-MM-DD).
            radius_m: Circular analysis radius in meters (default 500).
            cloud_probability_threshold: Max cloud probability cutoff % (default 65).

        Returns:
            Normalized SatelliteResponse object.

        Raises:
            InvalidCoordinatesError: On geographic coordinate out of bounds.
            InvalidDateRangeError: On invalid date strings or ordering.
            InvalidParameterError: On invalid radius or cloud threshold.
            EarthEngineAuthError: On missing or unauthenticated Earth Engine credentials.
            NoObservationsFoundError: When no cloud-free observations remain.
            EarthEngineExecutionError: On upstream query or reduction errors.
        """
        # 1. Validate inputs
        validate_coordinates(latitude, longitude)
        validate_date_range(start_date, end_date)
        validate_parameters(radius_m, cloud_probability_threshold)

        # 2. Execute Earth Engine computation asynchronously in thread pool to prevent event loop blocking
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self._execute_earth_engine_pipeline,
                    latitude=latitude,
                    longitude=longitude,
                    start_date=start_date,
                    end_date=end_date,
                    radius_m=radius_m,
                    cloud_probability_threshold=cloud_probability_threshold,
                ),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise EarthEngineExecutionError(
                f"Satellite service timed out while querying Earth Engine after {self.timeout_seconds}s."
            ) from exc

        usable_count = result["usable_observations"]
        raw_stats = result["stats"]

        # 3. Extract and sanitize statistics
        def _clamp(val: Any) -> float:
            if val is None:
                return 0.0
            return float(max(-1.0, min(1.0, round(float(val), 4))))

        def _safe_float(val: Any) -> float | None:
            if val is None:
                return None
            return round(float(val), 4)

        ndvi_med = _clamp(raw_stats.get("ndvi_median"))
        ndwi_med = _clamp(raw_stats.get("ndwi_median"))
        ndmi_med = _clamp(raw_stats.get("ndmi_median"))

        # Build detailed statistical dictionary
        stats_dict = {
            "ndvi": IndexStatistics(
                min=_safe_float(raw_stats.get("ndvi_min")),
                max=_safe_float(raw_stats.get("ndvi_max")),
                mean=_safe_float(raw_stats.get("ndvi_mean")),
                median=_safe_float(raw_stats.get("ndvi_median")),
                std_dev=_safe_float(raw_stats.get("ndvi_stdDev")),
            ),
            "ndwi": IndexStatistics(
                min=_safe_float(raw_stats.get("ndwi_min")),
                max=_safe_float(raw_stats.get("ndwi_max")),
                mean=_safe_float(raw_stats.get("ndwi_mean")),
                median=_safe_float(raw_stats.get("ndwi_median")),
                std_dev=_safe_float(raw_stats.get("ndwi_stdDev")),
            ),
            "ndmi": IndexStatistics(
                min=_safe_float(raw_stats.get("ndmi_min")),
                max=_safe_float(raw_stats.get("ndmi_max")),
                mean=_safe_float(raw_stats.get("ndmi_mean")),
                median=_safe_float(raw_stats.get("ndmi_median")),
                std_dev=_safe_float(raw_stats.get("ndmi_stdDev")),
            ),
        }

        # 4. Construct response
        return SatelliteResponse(
            latitude=round(latitude, 4),
            longitude=round(longitude, 4),
            radius_m=radius_m,
            start_date=start_date,
            end_date=end_date,
            usable_observations=usable_count,
            cloud_probability_threshold=cloud_probability_threshold,
            ndvi_median=ndvi_med,
            ndwi_median=ndwi_med,
            ndmi_median=ndmi_med,
            data_source="Sentinel-2",
            statistics=stats_dict,
        )


# Singleton instance for route injection
satellite_service = SatelliteService()
