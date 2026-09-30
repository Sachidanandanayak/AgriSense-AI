"""FastAPI router for satellite observation and spectral indices endpoints."""

from datetime import datetime
import logging
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.satellite import SatelliteResponse
from app.services.satellite_service import (
    satellite_service,
    InvalidCoordinatesError,
    InvalidDateRangeError,
    InvalidParameterError,
    EarthEngineAuthError,
    EarthEngineInitError,
    NoObservationsFoundError,
    EarthEngineExecutionError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/satellite",
    response_model=SatelliteResponse,
    summary="Get Sentinel-2 satellite vegetation and moisture indices by coordinates",
    description=(
        "Retrieves Sentinel-2 Harmonized Surface Reflectance observations for specified coordinates, "
        "filters cloudy pixels using S2 Cloud Probability, computes a median temporal composite across the "
        "requested date range, and aggregates key agricultural indices (NDVI, NDWI, NDMI) over a circular buffer."
    ),
    responses={
        200: {"description": "Successfully retrieved and aggregated satellite indices."},
        400: {"description": "Invalid coordinates, malformed date strings, or invalid query parameters."},
        404: {"description": "No suitable cloud-free Sentinel-2 observation found for coordinates and date range."},
        502: {"description": "Earth Engine upstream computation or aggregation error."},
        503: {"description": "Earth Engine authentication or service initialization unavailable."},
        504: {"description": "Earth Engine query timed out."},
    },
)
async def get_satellite_data(
    latitude: float = Query(
        ...,
        description="Latitude in decimal degrees (-90.0 to 90.0)",
        examples=[16.20],
    ),
    longitude: float = Query(
        ...,
        description="Longitude in decimal degrees (-180.0 to 180.0)",
        examples=[77.35],
    ),
    start_date: str = Query(
        ...,
        description="Start date for temporal composite in YYYY-MM-DD format",
        examples=["2026-09-01"],
    ),
    end_date: str = Query(
        ...,
        description="End date for temporal composite in YYYY-MM-DD format",
        examples=["2026-09-25"],
    ),
    radius_m: float = Query(
        default=500.0,
        description="Circular analysis radius around coordinate in meters (default 500m)",
        examples=[500.0],
    ),
    cloud_probability_threshold: float = Query(
        default=65.0,
        description="Pixel-level cloud probability cutoff percentage (0 to 100, default 65%)",
        examples=[65.0],
    ),
) -> SatelliteResponse:
    """Retrieve normalized Sentinel-2 indices and regional statistics for a target location."""
    # 1. Geographic coordinate validation
    if not (-90.0 <= latitude <= 90.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Latitude must be between -90.0 and 90.0 degrees. Received: {latitude}",
        )
    if not (-180.0 <= longitude <= 180.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Longitude must be between -180.0 and 180.0 degrees. Received: {longitude}",
        )

    # 2. Date format and ordering validation
    try:
        d_start = datetime.strptime(start_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid start_date '{start_date}'. Must be in YYYY-MM-DD format.",
        )

    try:
        d_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid end_date '{end_date}'. Must be in YYYY-MM-DD format.",
        )

    if d_start > d_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"start_date ({start_date}) must be less than or equal to end_date ({end_date}).",
        )

    # 3. Numeric parameter bounds
    if radius_m <= 0.0 or radius_m > 50000.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"radius_m ({radius_m}) must be a positive number between 10 and 50,000 meters.",
        )
    if not (0.0 <= cloud_probability_threshold <= 100.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"cloud_probability_threshold ({cloud_probability_threshold}) must be between 0.0 and 100.0 percent.",
        )

    # 4. Delegate to satellite service
    try:
        return await satellite_service.get_satellite_data(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            radius_m=radius_m,
            cloud_probability_threshold=cloud_probability_threshold,
        )
    except InvalidCoordinatesError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except InvalidDateRangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except InvalidParameterError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except NoObservationsFoundError as exc:
        logger.info("No satellite observations: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No suitable cloud-free Sentinel-2 observation was found for the requested location and date range.",
        ) from exc
    except EarthEngineAuthError as exc:
        logger.error("Earth Engine auth error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Earth Engine is not authenticated or project is not configured. Please configure EARTHENGINE_PROJECT or authenticate your environment.",
        ) from exc
    except EarthEngineInitError as exc:
        logger.error("Earth Engine init error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Earth Engine service is currently unavailable.",
        ) from exc
    except EarthEngineExecutionError as exc:
        logger.error("Earth Engine execution error: %s", exc)
        err_msg = str(exc)
        if "timed out" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Satellite service timed out while querying Earth Engine.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Earth Engine returned an error during index calculation or regional aggregation.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching satellite data: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing satellite data.",
        ) from exc
