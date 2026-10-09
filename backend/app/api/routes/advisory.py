"""FastAPI router for Evidence-Based Farm Advisory Engine endpoints."""

import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.advisory import (
    FarmAdvisoryRequest,
    FarmAdvisoryResponse,
)
from app.services.farm_advisory import (
    AdvisoryDataAlignmentError,
    AdvisoryServiceUnavailableError,
    CropRequirementNotFoundError,
    FarmAdvisoryError,
    InvalidAdvisoryRequestError,
    WaterAdvisoryCalculationError,
    farm_advisory_service,
)
from app.services.recommendation.exceptions import (
    IncompatibleFeatureSchemaError,
    InvalidCoordinatesError,
    InvalidDateError,
    MissingModelInputError,
    ModelPredictionError,
    ModelUnavailableError,
    RecommendationValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/advisory",
    response_model=FarmAdvisoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate evidence-based farm advisory report with FAO ecological compatibility",
    description=(
        "Converts benchmark Random Forest ML crop recommendations and multi-source environmental "
        "observations (Open-Meteo weather, Sentinel-2 satellite, ISRIC SoilGrids) into transparent, "
        "authoritative agricultural advisory evidence. Grounded in authoritative FAO ECOCROP "
        "crop ecological requirements and FAO-56 crop-water methodologies. "
        "Preserves exact ML probability estimates without converting them into arbitrary percentages. "
        "Produces transparent variable compatibility statuses (favorable, caution, unfavorable, unavailable), "
        "deterministic risk flags, growth cycle details, and explicit scientific limitations."
    ),
    responses={
        200: {"description": "Successfully generated evidence-based farm advisory report."},
        400: {"description": "Validation error: invalid coordinates, malformed date, or missing required parameters."},
        422: {"description": "Pydantic request validation failure."},
        503: {"description": "Service unavailable: trained model artifact missing or failed to initialize."},
        500: {"description": "Internal server error during advisory processing."},
    },
)
async def generate_farm_advisory(
    request: FarmAdvisoryRequest,
) -> FarmAdvisoryResponse:
    """Generate comprehensive farm advisory and FAO ecological compatibility report."""
    try:
        return await farm_advisory_service.generate_advisory(request)
    except (
        InvalidAdvisoryRequestError,
        InvalidCoordinatesError,
        InvalidDateError,
        MissingModelInputError,
        RecommendationValidationError,
        AdvisoryDataAlignmentError,
    ) as exc:
        logger.warning("Farm advisory request validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except (ModelUnavailableError, AdvisoryServiceUnavailableError) as exc:
        logger.error("Farm advisory service dependency unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Farm advisory service dependency is currently unavailable: {exc}",
        ) from exc
    except (IncompatibleFeatureSchemaError, ModelPredictionError, WaterAdvisoryCalculationError) as exc:
        logger.error("Advisory calculation failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Farm advisory generation failed during model prediction or compatibility evaluation.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error in farm advisory endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the farm advisory report.",
        ) from exc
