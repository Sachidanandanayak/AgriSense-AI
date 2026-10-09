"""Evidence-Based Farm Advisory Engine package for AgriSense AI."""

from app.services.farm_advisory.exceptions import (
    AdvisoryDataAlignmentError,
    AdvisoryServiceUnavailableError,
    CropRequirementNotFoundError,
    FarmAdvisoryError,
    InvalidAdvisoryRequestError,
    WaterAdvisoryCalculationError,
)
from app.services.farm_advisory.schemas import (
    ADVISORY_DISCLAIMER,
    CompatibilityStatus,
    CropAdvisoryItem,
    CropEnvironmentalRequirement,
    DataQualityAudit,
    FarmAdvisoryRequest,
    FarmAdvisoryResponse,
    RequirementProvenance,
    SatelliteEnvironmentalContext,
    VariableCompatibility,
    WaterAdvisory,
    WaterAdvisoryStatus,
)
from app.services.farm_advisory.requirements import (
    CropRequirementRepository,
    DEFAULT_ECOCROP_PROVENANCE,
    FAO_ECOCROP_PROFILES,
    crop_requirement_repository,
)
from app.services.farm_advisory.compatibility import (
    classify_soil_texture_group,
    evaluate_crop_environmental_compatibility,
    evaluate_numeric_range,
    evaluate_soil_texture,
)
from app.services.farm_advisory.water_advisory import (
    calculate_fao56_penman_monteith,
    evaluate_water_advisory,
)
from app.services.farm_advisory.explanation import (
    generate_advisory_explanations,
    generate_advisory_limitations,
)
from app.services.farm_advisory.validators import (
    audit_data_freshness,
    validate_advisory_coordinates,
    validate_advisory_date,
)
from app.services.farm_advisory.advisory_service import (
    FarmAdvisoryService,
    farm_advisory_service,
)

__all__ = [
    "FarmAdvisoryError",
    "InvalidAdvisoryRequestError",
    "CropRequirementNotFoundError",
    "AdvisoryDataAlignmentError",
    "WaterAdvisoryCalculationError",
    "AdvisoryServiceUnavailableError",
    "ADVISORY_DISCLAIMER",
    "CompatibilityStatus",
    "CropAdvisoryItem",
    "CropEnvironmentalRequirement",
    "DataQualityAudit",
    "FarmAdvisoryRequest",
    "FarmAdvisoryResponse",
    "RequirementProvenance",
    "SatelliteEnvironmentalContext",
    "VariableCompatibility",
    "WaterAdvisory",
    "WaterAdvisoryStatus",
    "CropRequirementRepository",
    "DEFAULT_ECOCROP_PROVENANCE",
    "FAO_ECOCROP_PROFILES",
    "crop_requirement_repository",
    "classify_soil_texture_group",
    "evaluate_crop_environmental_compatibility",
    "evaluate_numeric_range",
    "evaluate_soil_texture",
    "calculate_fao56_penman_monteith",
    "evaluate_water_advisory",
    "generate_advisory_explanations",
    "generate_advisory_limitations",
    "audit_data_freshness",
    "validate_advisory_coordinates",
    "validate_advisory_date",
    "FarmAdvisoryService",
    "farm_advisory_service",
]
