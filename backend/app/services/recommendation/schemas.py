"""Pydantic schemas and contracts for Crop Suitability & Recommendation Engine."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.schemas.weather import WeatherResponse
from app.schemas.satellite import SatelliteResponse
from app.schemas.soil import SoilResponse

MANDATORY_DISCLAIMER: str = (
    "The current recommendation engine is a benchmark-model recommendation layer "
    "augmented with environmental context. It is not yet a field-validated crop "
    "suitability or yield prediction system."
)


class AgriculturalInput(BaseModel):
    """Agricultural and soil nutrient inputs required by the benchmark ML model."""

    nitrogen: float = Field(
        ...,
        ge=0.0,
        description="Available Nitrogen (N) content in soil (kg/ha)",
    )
    phosphorus: float = Field(
        ...,
        ge=0.0,
        description="Available Phosphorus (P) content in soil (kg/ha)",
    )
    potassium: float = Field(
        ...,
        ge=0.0,
        description="Available Potassium (K) content in soil (kg/ha)",
    )
    temperature: float = Field(
        ...,
        ge=-20.0,
        le=60.0,
        description="Seasonal or measured ambient temperature (°C)",
    )
    humidity: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Relative humidity percentage (0-100%)",
    )
    ph: float = Field(
        ...,
        ge=0.0,
        le=14.0,
        description="Soil pH value on standard 0-14 scale",
    )
    rainfall: float = Field(
        ...,
        ge=0.0,
        description="Seasonal or measured rainfall (mm)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nitrogen": 80.0,
                "phosphorus": 40.0,
                "potassium": 40.0,
                "temperature": 26.5,
                "humidity": 65.0,
                "ph": 6.8,
                "rainfall": 120.0,
            }
        }
    )


class RecommendationRequest(BaseModel):
    """Inbound request schema for farmer-facing crop recommendations."""

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in WGS84 decimal degrees (-90.0 to 90.0)",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in WGS84 decimal degrees (-180.0 to 180.0)",
    )
    observation_date: str | None = Field(
        default=None,
        description="Target observation / planting reference date (YYYY-MM-DD)",
    )
    agricultural_inputs: AgriculturalInput | None = Field(
        default=None,
        description="Agricultural nutrient and climate parameters required for benchmark model inference",
    )

    # Flat convenience parameters mapped to agricultural_inputs via pre-validator
    nitrogen: float | None = Field(default=None, ge=0.0)
    phosphorus: float | None = Field(default=None, ge=0.0)
    potassium: float | None = Field(default=None, ge=0.0)
    temperature: float | None = Field(default=None, ge=-20.0, le=60.0)
    humidity: float | None = Field(default=None, ge=0.0, le=100.0)
    ph: float | None = Field(default=None, ge=0.0, le=14.0)
    rainfall: float | None = Field(default=None, ge=0.0)

    top_k: int = Field(
        default=3,
        ge=1,
        le=22,
        description="Number of top crop recommendations to return (default: 3)",
    )

    # Optional pre-fetched environmental context objects
    weather_context: WeatherResponse | None = Field(
        default=None,
        description="Optional pre-fetched weather observation",
    )
    satellite_context: SatelliteResponse | None = Field(
        default=None,
        description="Optional pre-fetched Sentinel-2 satellite indices",
    )
    soil_context: SoilResponse | None = Field(
        default=None,
        description="Optional pre-fetched ISRIC SoilGrids 2.0 properties",
    )

    # Dynamic live-fetching flags (when context objects are not provided)
    fetch_live_weather: bool = Field(
        default=False,
        description="If True and weather_context is None, attempt live weather query",
    )
    fetch_live_satellite: bool = Field(
        default=False,
        description="If True and satellite_context is None, attempt live Sentinel-2 query",
    )
    fetch_live_soil: bool = Field(
        default=False,
        description="If True and soil_context is None, attempt live SoilGrids query",
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
                    # If all 7 keys are present in flat form, build agricultural_inputs
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


class CropRecommendationItem(BaseModel):
    """Ranked crop recommendation item with benchmark-model probability estimate."""

    crop: str = Field(
        ...,
        description="Recommended crop variety identifier (e.g., 'rice', 'maize')",
    )
    rank: int = Field(
        ...,
        ge=1,
        description="Rank position based on benchmark model probability (1 = highest)",
    )
    probability_estimate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Benchmark-model probability estimate (0.0 to 1.0). NOT a field-validated suitability score.",
    )
    confidence_percentage: str = Field(
        ...,
        description="Formatted model confidence percentage string (e.g., '84.50%')",
    )


class EnvironmentalContext(BaseModel):
    """Multi-source environmental indicators providing contextual agronomic reference."""

    weather: WeatherResponse | None = Field(
        default=None,
        description="Meteorological observations at or near target coordinates",
    )
    satellite: SatelliteResponse | None = Field(
        default=None,
        description="Sentinel-2 vegetation and moisture indices (NDVI, NDWI, NDMI)",
    )
    soil: SoilResponse | None = Field(
        default=None,
        description="ISRIC SoilGrids 2.0 digital soil mapping predictions",
    )


class DataQualityReport(BaseModel):
    """Data provenance and source availability audit for the recommendation response."""

    model_available: bool = Field(
        default=True,
        description="Whether the benchmark Random Forest model was successfully loaded and executed",
    )
    model_version: str = Field(
        default="crop_recommendation_rf_v1",
        description="Benchmark ML model identifier and version",
    )
    weather_available: bool = Field(
        default=False,
        description="Indicates whether meteorological context was supplied or retrieved",
    )
    satellite_available: bool = Field(
        default=False,
        description="Indicates whether satellite remote sensing context was supplied or retrieved",
    )
    soil_available: bool = Field(
        default=False,
        description="Indicates whether digital soil mapping context was supplied or retrieved",
    )
    missing_sources: list[str] = Field(
        default_factory=list,
        description="List of environmental sources unavailable for this recommendation",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Data quality warnings, spatial alignment notes, or temporal gap alerts",
    )


class RecommendationResponse(BaseModel):
    """Production response schema for crop suitability recommendations."""

    latitude: float = Field(
        ...,
        description="Target latitude in WGS84 decimal degrees",
    )
    longitude: float = Field(
        ...,
        description="Target longitude in WGS84 decimal degrees",
    )
    observation_date: str | None = Field(
        default=None,
        description="Target observation or reference date",
    )
    recommendations: list[CropRecommendationItem] = Field(
        ...,
        description="Ranked list of crop recommendations ordered by benchmark model probability estimate",
    )
    environmental_context: EnvironmentalContext = Field(
        default_factory=EnvironmentalContext,
        description="Supporting environmental context from weather, satellite, and soil data sources",
    )
    data_quality: DataQualityReport = Field(
        default_factory=DataQualityReport,
        description="Data quality, source availability, and provenance metadata",
    )
    explanation: list[str] = Field(
        default_factory=list,
        description="Transparent, data-grounded explanations explaining recommendation drivers and context",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Explicit scientific caveats and operational limitations of the benchmark model",
    )
    model_input_features: dict[str, float] = Field(
        default_factory=dict,
        description="Exact 11 features consumed by the benchmark Random Forest model in training order",
    )
    disclaimer: str = Field(
        default=MANDATORY_DISCLAIMER,
        description="Mandatory scientific interpretation advisory notice",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "latitude": 16.20,
                "longitude": 77.35,
                "observation_date": "2026-09-25",
                "recommendations": [
                    {
                        "crop": "rice",
                        "rank": 1,
                        "probability_estimate": 0.88,
                        "confidence_percentage": "88.00%",
                    },
                    {
                        "crop": "jute",
                        "rank": 2,
                        "probability_estimate": 0.08,
                        "confidence_percentage": "8.00%",
                    },
                    {
                        "crop": "cotton",
                        "rank": 3,
                        "probability_estimate": 0.02,
                        "confidence_percentage": "2.00%",
                    },
                ],
                "environmental_context": {
                    "weather": None,
                    "satellite": None,
                    "soil": None,
                },
                "data_quality": {
                    "model_available": True,
                    "model_version": "crop_recommendation_rf_v1",
                    "weather_available": False,
                    "satellite_available": False,
                    "soil_available": False,
                    "missing_sources": ["weather", "satellite", "soil"],
                    "warnings": [],
                },
                "explanation": [
                    "The benchmark Random Forest model ranked 'rice' highest (probability estimate: 88.00%) based on the supplied agricultural nutrient and climate inputs.",
                    "Weather, satellite, and soil contexts were not available for this run; recommendations rely exclusively on supplied agricultural inputs.",
                ],
                "limitations": [
                    "The current recommendation engine is a benchmark-model recommendation layer augmented with environmental context. It is not yet a field-validated crop suitability or yield prediction system.",
                ],
                "model_input_features": {
                    "N": 80.0,
                    "P": 40.0,
                    "K": 40.0,
                    "temperature": 26.5,
                    "humidity": 65.0,
                    "ph": 6.8,
                    "rainfall": 120.0,
                    "N_P_ratio": 2.0,
                    "N_K_ratio": 2.0,
                    "P_K_ratio": 1.0,
                    "rain_temp_ratio": 4.5283,
                },
                "disclaimer": MANDATORY_DISCLAIMER,
            }
        },
    )
