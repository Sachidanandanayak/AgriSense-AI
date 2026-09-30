"""FastAPI router for soil property observation endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.soil import SoilResponse
from app.services.soil_provider import (
    SUPPORTED_DEPTH_INTERVALS,
    SoilProviderError,
    SoilProviderTimeoutError,
    SoilProviderConnectionError,
    SoilProviderRateLimitError,
    SoilProviderUnavailableError,
    MalformedSoilResponseError,
    NoSoilDataError,
)
from app.services.soil_service import (
    soil_service,
    InvalidCoordinatesError,
    InvalidDepthError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/soil",
    response_model=SoilResponse,
    summary="Get normalized soil properties by coordinates and depth interval",
    description=(
        "Retrieves digital soil property predictions from ISRIC SoilGrids 2.0 (~250m resolution) "
        "for specified latitude and longitude coordinates. Normalizes raw integer-mapped values "
        "into conventional agronomic units (pH, % clay, % sand, % silt, organic carbon, bulk density, CEC, nitrogen)."
    ),
    responses={
        200: {"description": "Successfully retrieved and normalized soil properties."},
        400: {"description": "Invalid geographic coordinates or unsupported depth interval."},
        404: {"description": "No soil data available for coordinates (e.g. water body, unmodeled mask)."},
        429: {"description": "Upstream SoilGrids rate limit exceeded."},
        502: {"description": "SoilGrids provider returned an unexpected or malformed response."},
        503: {"description": "SoilGrids service temporarily unavailable or unreachable."},
        504: {"description": "SoilGrids request timed out."},
    },
)
async def get_soil(
    latitude: float = Query(
        ...,
        description="Latitude in decimal degrees (-90.0 to 90.0)",
        examples=[20.59],
    ),
    longitude: float = Query(
        ...,
        description="Longitude in decimal degrees (-180.0 to 180.0)",
        examples=[78.96],
    ),
    depth: str = Query(
        default="0-5cm",
        description="Standard depth interval (0-5cm, 5-15cm, 15-30cm, 30-60cm, 60-100cm, 100-200cm)",
        examples=["0-5cm"],
    ),
) -> SoilResponse:
    """Retrieve normalized soil physical and chemical properties for a target location."""
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

    # 2. Depth interval validation
    cleaned_depth = depth.strip().lower()
    if cleaned_depth not in SUPPORTED_DEPTH_INTERVALS:
        supported_str = ", ".join(sorted(SUPPORTED_DEPTH_INTERVALS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported depth interval '{depth}'. Supported intervals: {supported_str}",
        )

    # 3. Delegate to soil service
    try:
        return await soil_service.get_soil_data(
            latitude=latitude,
            longitude=longitude,
            depth_interval=cleaned_depth,
        )
    except InvalidCoordinatesError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except InvalidDepthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except NoSoilDataError as exc:
        logger.info("No soil data for location (%s, %s): %s", latitude, longitude, exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No soil data available from SoilGrids for the requested coordinates (location may be a water body, unmodeled area, or outside coverage).",
        ) from exc
    except SoilProviderTimeoutError as exc:
        logger.error("Soil provider timeout: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Soil data service timed out while querying SoilGrids provider.",
        ) from exc
    except SoilProviderRateLimitError as exc:
        logger.warning("Soil provider rate limit: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Soil data provider rate limit exceeded. Please try again later adhering to fair use.",
        ) from exc
    except (SoilProviderUnavailableError, SoilProviderConnectionError) as exc:
        logger.error("Soil provider unavailable / connection error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Soil data service is temporarily unavailable due to upstream connectivity or server issues.",
        ) from exc
    except MalformedSoilResponseError as exc:
        logger.error("Soil provider malformed response: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Soil data provider returned an unexpected or malformed response.",
        ) from exc
    except SoilProviderError as exc:
        logger.error("Soil provider generic error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Soil data provider returned an unexpected error response.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching soil data: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing soil data.",
        ) from exc
