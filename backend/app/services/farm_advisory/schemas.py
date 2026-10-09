"""Pydantic schemas and contracts for Evidence-Based Farm Advisory Engine."""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.satellite import SatelliteResponse
from app.schemas.soil import SoilResponse
from app.schemas.weather import WeatherResponse
from app.services.recommendation.schemas import (
    AgriculturalInput,
    EnvironmentalContext,
    RecommendationRequest,
    RecommendationResponse,
)

ADVISORY_DISCLAIMER: str = (
    "This farm advisory report synthesizes benchmark machine learning recommendations "
    "with authoritative FAO ECOCROP ecological requirements and observed environmental context. "
    "The benchmark model probability estimate reflects classification likelihood relative to its "
    "training trial distribution and does NOT represent a scientifically validated crop suitability, "
    "commercial yield, or harvest success guarantee. Agronomic suitability evaluations indicate "
    "compatibility against documented FAO ecological ranges and must be interpreted alongside local "
    "agricultural extension advice, certified soil tests, cultivar specifics, and farm management practices."
)


class CompatibilityStatus(str, Enum):
    """Categorical compatibility status against documented authoritative ranges."""

    FAVORABLE = "favorable"
    CAUTION = "caution"
    UNFAVORABLE = "unfavorable"
    UNAVAILABLE = "unavailable"


class WaterAdvisoryStatus(str, Enum):
    """Status of water-related advisory calculation."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class RequirementProvenance(BaseModel):
    """Audit provenance for source-backed crop ecological requirements."""

    source_name: str = Field(
        default="FAO ECOCROP - Crop Ecological Requirements Database",
        description="Authoritative organization and database name",
    )
    source_url: str = Field(
        default="https://ecocrop.apps.fao.org/ecocrop/srv/en/home",
        description="Authoritative reference URL or permanent portal",
    )
    source_field: str | None = Field(
        default=None,
        description="Database variable codes (e.g. TOPMN, TOPMX, TMIN, TMAX, ROPMN, ROPMX, RMIN, RMAX, PHOPMN, PHOPMX, PHMIN, PHMAX)",
    )
    source_version_or_reference: str | None = Field(
        default="FAO EcoCrop Database / FAO GAEZ (Global Agro-Ecological Zoning) v4 biophysical descriptors",
        description="Database release version or authoritative publication citation",
    )
    notes: str | None = Field(
        default="Authoritative agro-ecological parameters define macro-scale biophysical tolerance boundaries. Microclimate, cultivar genetics, and local management practices may modify local thresholds.",
        description="Operational context, known boundary conditions, or source limitations",
    )


class CropEnvironmentalRequirement(BaseModel):
    """Authoritative source-backed ecological profile for a crop species."""

    crop_name: str = Field(..., description="Standardized lowercase crop key (e.g. 'rice', 'maize')")
    scientific_name: str = Field(..., description="Botanical binomial nomenclature (e.g. 'Oryza sativa')")
    ecocrop_code: int | None = Field(default=None, description="Official FAO ECOCROP species identifier code")
    common_name: str | None = Field(default=None, description="Primary common name documented in FAO ECOCROP")

    # Thermal boundaries (°C)
    temp_min_c: float | None = Field(default=None, description="Absolute minimum temperature for crop survival (TMIN)")
    temp_opt_min_c: float | None = Field(default=None, description="Optimal lower temperature boundary (TOPMN)")
    temp_opt_max_c: float | None = Field(default=None, description="Optimal upper temperature boundary (TOPMX)")
    temp_max_c: float | None = Field(default=None, description="Absolute maximum temperature for crop survival (TMAX)")

    # Precipitation / Rainfall boundaries (mm)
    rainfall_min_mm: float | None = Field(default=None, description="Absolute minimum rainfall for growth (RMIN)")
    rainfall_opt_min_mm: float | None = Field(default=None, description="Optimal lower rainfall boundary (ROPMN)")
    rainfall_opt_max_mm: float | None = Field(default=None, description="Optimal upper rainfall boundary (ROPMX)")
    rainfall_max_mm: float | None = Field(default=None, description="Absolute maximum rainfall tolerated (RMAX)")

    # Soil pH boundaries (standard 0-14 scale)
    soil_ph_min: float | None = Field(default=None, description="Absolute minimum tolerable soil pH (PHMIN)")
    soil_ph_opt_min: float | None = Field(default=None, description="Optimal lower soil pH boundary (PHOPMN)")
    soil_ph_opt_max: float | None = Field(default=None, description="Optimal upper soil pH boundary (PHOPMX)")
    soil_ph_max: float | None = Field(default=None, description="Absolute maximum tolerable soil pH (PHMAX)")

    # Soil physical and chemical descriptors
    soil_textures_optimal: list[str] | None = Field(default=None, description="Optimal soil texture classes (e.g. ['medium', 'heavy'])")
    soil_textures_absolute: list[str] | None = Field(default=None, description="Absolute tolerable soil texture classes")
    soil_drainage_optimal: str | None = Field(default=None, description="Optimal drainage condition (e.g. 'well (dry spells)')")
    soil_drainage_absolute: str | None = Field(default=None, description="Absolute tolerable drainage condition")
    soil_depth_optimal: str | None = Field(default=None, description="Optimal root depth (e.g. 'deep (>>150 cm)')")
    soil_depth_absolute: str | None = Field(default=None, description="Absolute tolerable soil depth")
    soil_fertility_optimal: str | None = Field(default=None, description="Optimal soil fertility requirement (high, moderate, low)")
    soil_salinity_optimal: str | None = Field(default=None, description="Salinity tolerance threshold (e.g. 'low (<4 dS/m)')")

    # Crop cycle duration (days)
    crop_cycle_min_days: int | None = Field(default=None, description="Minimum crop cycle duration in days (GMIN)")
    crop_cycle_max_days: int | None = Field(default=None, description="Maximum crop cycle duration in days (GMAX)")

    provenance: RequirementProvenance = Field(
        default_factory=RequirementProvenance,
        description="Source provenance metadata verifying authoritative origin",
    )


class VariableCompatibility(BaseModel):
    """Transparent comparison of an observed environmental variable against documented requirements."""

    variable: str = Field(..., description="Evaluated variable identifier (e.g. 'temperature', 'rainfall', 'soil_ph')")
    status: CompatibilityStatus = Field(..., description="Categorical evaluation status: favorable, caution, unfavorable, or unavailable")
    observed_value: Any | None = Field(default=None, description="Actual observed or measured value from environmental context")
    observed_unit: str | None = Field(default=None, description="Unit of measurement (°C, mm, pH units, etc.)")
    documented_optimal_range: str | None = Field(default=None, description="Documented optimal range from authoritative source")
    documented_absolute_range: str | None = Field(default=None, description="Documented absolute tolerance range from authoritative source")
    reason: str = Field(..., description="Clear, non-technical explanation justifying the assigned compatibility status")
    source: str = Field(default="FAO ECOCROP", description="Authoritative reference providing the agronomic threshold")


class WaterAdvisory(BaseModel):
    """Defensible water-related advisory based strictly on authoritative FAO methodologies."""

    status: WaterAdvisoryStatus = Field(
        default=WaterAdvisoryStatus.UNAVAILABLE,
        description="Whether a defensible FAO-56 crop-water calculation could be computed",
    )
    methodology: str = Field(
        default="FAO-56 Penman-Monteith / FAO CROPWAT Methodology",
        description="Authoritative reference methodology utilized",
    )
    reference_evapotranspiration_et0_mm_day: float | None = Field(
        default=None,
        description="Daily reference evapotranspiration (ET0) in mm/day if defensibly computed",
    )
    crop_coefficient_kc: float | None = Field(
        default=None,
        description="Growth stage-specific crop coefficient (Kc) if documented and supplied",
    )
    crop_evapotranspiration_etc_mm_day: float | None = Field(
        default=None,
        description="Crop evapotranspiration demand (ETc = Kc * ET0) in mm/day if computed",
    )
    estimated_irrigation_requirement_mm: float | None = Field(
        default=None,
        description="Net irrigation water requirement (ETc - Peff) in mm if computed",
    )
    reason: str = Field(
        ...,
        description="Agronomic justification explaining calculation outcome or missing parameters",
    )
    missing_parameters: list[str] = Field(
        default_factory=list,
        description="Specific missing parameters preventing defensible FAO-56 calculation",
    )
    notes: str = Field(
        default="Under FAO-56 methodology, reference evapotranspiration requires net solar radiation, daily temperature extrema, standardized 2m wind speed, and vapor pressure. Stage-specific crop water demand requires growth stage Kc values. Instantaneous current rainfall or temperature observations cannot be substituted for total seasonal crop water requirements.",
        description="Scientific limitations and operational guidance",
    )


class SatelliteEnvironmentalContext(BaseModel):
    """Contextual vegetation and moisture indicators derived from Sentinel-2 remote sensing."""

    available: bool = Field(default=False, description="Whether Sentinel-2 satellite indices were retrieved")
    observation_window: str | None = Field(default=None, description="Start and end dates of satellite imagery compositing")
    usable_observations: int | None = Field(default=None, description="Number of cloud-filtered Sentinel-2 scenes in window")
    ndvi_median: float | None = Field(default=None, description="Normalized Difference Vegetation Index median (canopy greenness / biomass vigor)")
    ndwi_median: float | None = Field(default=None, description="Normalized Difference Water Index median (open water / plant surface water)")
    ndmi_median: float | None = Field(default=None, description="Normalized Difference Moisture Index median (canopy moisture stress)")
    summary: str = Field(..., description="Descriptive environmental summary of remote sensing observations")
    disclaimer: str = Field(
        default="Remote sensing indices (NDVI, NDWI, NDMI) serve strictly as environmental context indicators of canopy vigor and surface moisture; they do not constitute scientific proof of crop suitability, pest immunity, or harvest yield.",
        description="Mandatory satellite interpretation caveat",
    )


class CropAdvisoryItem(BaseModel):
    """Evidence-based agronomic advisory for a recommended crop candidate."""

    crop: str = Field(..., description="Crop identifier (e.g. 'rice', 'maize')")
    scientific_name: str | None = Field(default=None, description="Botanical binomial name")
    rank: int = Field(..., ge=1, description="Rank from benchmark ML recommendation")
    probability_estimate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Benchmark-model probability estimate preserved exactly from Phase 8. NOT a suitability score.",
    )
    confidence_percentage: str = Field(..., description="Formatted benchmark-model confidence percentage (e.g. '88.00%')")
    overall_compatibility: CompatibilityStatus = Field(
        ...,
        description="Deterministic overall compatibility status across documented environmental requirements",
    )
    compatibility_evaluations: dict[str, VariableCompatibility] = Field(
        default_factory=dict,
        description="Transparent variable-by-variable evaluations (temperature, rainfall, soil_ph, soil_texture, etc.)",
    )
    growth_cycle_days: str | None = Field(
        default=None,
        description="Documented crop growth cycle duration from FAO ECOCROP",
    )
    risk_flags: list[str] = Field(
        default_factory=list,
        description="Deterministic risk indicators identified for this crop under observed conditions",
    )
    advisory_notes: list[str] = Field(
        default_factory=list,
        description="Agronomic advisory notes explaining environmental compatibility and risk mitigation",
    )
    requirement_provenance: RequirementProvenance | None = Field(
        default=None,
        description="Authoritative source provenance for this crop's requirements",
    )


class DataQualityAudit(BaseModel):
    """Audit of data source availability, freshness, and operational flags."""

    model_available: bool = Field(default=True, description="Whether benchmark recommendation model executed")
    weather_available: bool = Field(default=False, description="Whether meteorological context was available")
    satellite_available: bool = Field(default=False, description="Whether Sentinel-2 satellite context was available")
    soil_available: bool = Field(default=False, description="Whether ISRIC SoilGrids data was available")
    missing_sources: list[str] = Field(default_factory=list, description="List of unavailable environmental data sources")
    stale_sources: list[str] = Field(default_factory=list, description="List of data sources exceeding freshness windows")
    risk_flags: list[str] = Field(default_factory=list, description="Global risk flags aggregated across all components")
    warnings: list[str] = Field(default_factory=list, description="Operational warnings or alignment notices")


class FarmAdvisoryRequest(BaseModel):
    """Inbound request schema for Evidence-Based Farm Advisory Engine."""

    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in WGS84 decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in WGS84 decimal degrees")
    observation_date: str | None = Field(default=None, description="Target observation / planting reference date (YYYY-MM-DD)")

    # Agricultural nutrient and climate inputs
    agricultural_inputs: AgriculturalInput | None = Field(
        default=None,
        description="Nutrient and environmental inputs required by benchmark model and agronomic checks",
    )

    # Flat convenience inputs
    nitrogen: float | None = Field(default=None, ge=0.0)
    phosphorus: float | None = Field(default=None, ge=0.0)
    potassium: float | None = Field(default=None, ge=0.0)
    temperature: float | None = Field(default=None, ge=-20.0, le=60.0)
    humidity: float | None = Field(default=None, ge=0.0, le=100.0)
    ph: float | None = Field(default=None, ge=0.0, le=14.0)
    rainfall: float | None = Field(default=None, ge=0.0)

    top_k: int = Field(default=3, ge=1, le=22, description="Number of crop recommendations to analyze")

    # Optional pre-fetched environmental context objects
    weather_context: WeatherResponse | None = Field(default=None)
    satellite_context: SatelliteResponse | None = Field(default=None)
    soil_context: SoilResponse | None = Field(default=None)

    # Live-fetching flags
    fetch_live_weather: bool = Field(default=False)
    fetch_live_satellite: bool = Field(default=False)
    fetch_live_soil: bool = Field(default=False)

    # Optional pre-existing Phase 8 recommendation response (allows analyzing existing recommendations without re-running model)
    recommendation_response: RecommendationResponse | None = Field(
        default=None,
        description="Optional pre-computed Phase 8 recommendation response to attach advisory evidence to without re-running ML inference",
    )

    # Optional detailed FAO-56 inputs (when user provides full parameters for water advisory)
    fao56_water_inputs: dict[str, float] | None = Field(
        default=None,
        description="Optional detailed meteorological and agronomic parameters for FAO-56 ET0 and crop water calculation",
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_agricultural_inputs(cls, data: Any) -> Any:
        """Allow flat agricultural fields to populate agricultural_inputs if not explicitly structured."""
        if isinstance(data, dict):
            agri = data.get("agricultural_inputs")
            if agri is None:
                flat_keys = [
                    "nitrogen",
                    "phosphorus",
                    "potassium",
                    "temperature",
                    "humidity",
                    "ph",
                    "rainfall",
                ]
                if any(k in data and data[k] is not None for k in flat_keys):
                    agri_dict = {k: data[k] for k in flat_keys if k in data and data[k] is not None}
                    if all(k in agri_dict for k in flat_keys):
                        data["agricultural_inputs"] = agri_dict
        return data

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "latitude": 16.20,
                "longitude": 77.35,
                "observation_date": "2026-09-25",
                "agricultural_inputs": {
                    "nitrogen": 80.0,
                    "phosphorus": 40.0,
                    "potassium": 40.0,
                    "temperature": 26.5,
                    "humidity": 65.0,
                    "ph": 6.8,
                    "rainfall": 120.0,
                },
                "top_k": 3,
                "fetch_live_weather": False,
                "fetch_live_satellite": False,
                "fetch_live_soil": False,
            }
        },
    )


class FarmAdvisoryResponse(BaseModel):
    """Production response schema for Evidence-Based Farm Advisory Engine."""

    latitude: float = Field(..., description="Target latitude coordinate in WGS84 decimal degrees")
    longitude: float = Field(..., description="Target longitude coordinate in WGS84 decimal degrees")
    observation_date: str | None = Field(default=None, description="Observation or reference planting date")
    crop_advisories: list[CropAdvisoryItem] = Field(
        ...,
        description="Ranked candidate crops with benchmark ML confidence estimates, source-backed compatibility evaluations, risk flags, and advisory notes",
    )
    water_advisory: WaterAdvisory = Field(
        ...,
        description="Scientifically defensible crop water requirement advisory based on FAO methodology",
    )
    satellite_context: SatelliteEnvironmentalContext | None = Field(
        default=None,
        description="Supporting Sentinel-2 vegetation and moisture context indicators with mandatory caveats",
    )
    risk_flags: list[str] = Field(
        default_factory=list,
        description="Consolidated deterministic risk indicators identified across farm conditions and crop requirements",
    )
    environmental_context: EnvironmentalContext = Field(
        default_factory=EnvironmentalContext,
        description="Raw normalized environmental observations (weather, satellite, soil)",
    )
    data_quality: DataQualityAudit = Field(
        default_factory=DataQualityAudit,
        description="Data provenance audit, source availability, staleness checks, and warnings",
    )
    explanations: list[str] = Field(
        default_factory=list,
        description="Transparent agronomic explanations explaining compatibility drivers and evidence",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Explicit scientific caveats, benchmark model boundaries, and operational limitations",
    )
    disclaimer: str = Field(
        default=ADVISORY_DISCLAIMER,
        description="Mandatory scientific advisory notice regarding ML benchmark nature and source provenance",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )
