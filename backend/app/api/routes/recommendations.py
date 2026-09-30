"""FastAPI router for Crop Suitability & Recommendation Engine endpoints."""

import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation import (
    IncompatibleFeatureSchemaError,
    InvalidCoordinatesError,
    InvalidDateError,
    MissingModelInputError,
    ModelPredictionError,
    ModelUnavailableError,
    RecommendationValidationError,
    recommendation_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate ranked crop recommendations with environmental context",
    description=(
        "Orchestrates benchmark Random Forest ML model inference with live or cached "
        "meteorological, Sentinel-2 satellite, and ISRIC SoilGrids data. "
        "Returns top-K recommended crops with model probability estimates, "
        "supporting environmental context, data provenance, missing-data warnings, "
        "and explicit scientific limitations."
    ),
    responses={
        200: {"description": "Successfully generated ranked crop recommendations."},
        400: {"description": "Validation error: invalid coordinates, malformed date, or missing required model inputs."},
        422: {"description": "Pydantic schema validation failure."},
        503: {"description": "Model service unavailable: trained model artifact missing or failed to initialize."},
        500: {"description": "Internal server error during recommendation inference."},
    },
)
async def generate_crop_recommendations(
    request: RecommendationRequest,
) -> RecommendationResponse:
    """Generate ranked crop suitability recommendations for a farm coordinate."""
    try:
        return await recommendation_service.generate_recommendation(request)
    except (
        InvalidCoordinatesError,
        InvalidDateError,
        MissingModelInputError,
        RecommendationValidationError,
    ) as exc:
        logger.warning("Recommendation request validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ModelUnavailableError as exc:
        logger.error("Crop recommendation model unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Crop recommendation model is currently unavailable: {exc}",
        ) from exc
    except (IncompatibleFeatureSchemaError, ModelPredictionError) as exc:
        logger.error("Model prediction failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model prediction failed while processing feature schema.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error in crop recommendation endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating crop recommendations.",
        ) from exc
