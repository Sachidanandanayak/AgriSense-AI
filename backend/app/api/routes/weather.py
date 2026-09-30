"""FastAPI router for weather observation and forecast endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.weather import WeatherResponse
from app.services.weather_service import (
    weather_service,
    InvalidCoordinatesError,
    WeatherTimeoutError,
    WeatherConnectionError,
    WeatherRateLimitError,
    WeatherProviderError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/weather",
    response_model=WeatherResponse,
    summary="Get current normalized weather by coordinates",
    description=(
        "Retrieves current meteorological observations for specified latitude and longitude "
        "coordinates, returning normalized temperature, humidity, rainfall, wind speed, and timestamp."
    ),
    responses={
        200: {"description": "Successfully retrieved and normalized weather data."},
        400: {"description": "Invalid geographic coordinates supplied."},
        429: {"description": "Weather provider rate limit exceeded."},
        502: {"description": "Weather provider returned an unexpected or error response."},
        503: {"description": "Weather service temporarily unavailable (network failure)."},
        504: {"description": "Weather provider request timed out."},
    },
)
async def get_weather(
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
) -> WeatherResponse:
    """Retrieve normalized current weather observations for a target location."""
    # Explicit coordinate boundary verification for informative 400 Bad Request
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

    try:
        return await weather_service.get_current_weather(
            latitude=latitude, longitude=longitude
        )
    except InvalidCoordinatesError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except WeatherTimeoutError as exc:
        logger.error("Weather timeout error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Weather service timed out while contacting upstream provider.",
        ) from exc
    except WeatherRateLimitError as exc:
        logger.warning("Weather rate limit error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Weather provider rate limit exceeded. Please try again later.",
        ) from exc
    except WeatherConnectionError as exc:
        logger.error("Weather network/connection error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weather service is temporarily unavailable due to network issues.",
        ) from exc
    except WeatherProviderError as exc:
        logger.error("Weather provider error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Weather provider returned an invalid or error response.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching weather: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing weather data.",
        ) from exc
