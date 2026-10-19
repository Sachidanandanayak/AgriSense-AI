"""Pydantic schemas and enums for Regional Agricultural Knowledge Base (Raichur & Yadgir, Karnataka)."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class SoilType(str, Enum):
    """Farmer-confirmed field soil taxonomy classification."""

    DEEP_BLACK = "deep_black"  # Vertisols / Deep black cotton soil (Yerri Bhumi)
    MEDIUM_BLACK = "medium_black"  # Medium black soil / Inceptisols
    RED_SANDY_LOAM = "red_sandy_loam"  # Alfisols / Chalka soil (Masab / Erra Bhumi)
    LOAM = "loam"  # Mixed Alluvial / Loamy soil


class IrrigationStatus(str, Enum):
    """Farmer-confirmed field water supply / irrigation access."""

    RAINFED = "rainfed"  # Dryland monsoon-dependent (no assured irrigation)
    CANAL_IRRIGATED = "canal_irrigated"  # Tungabhadra Left Bank Canal / Upper Krishna Project
    BOREWELL_IRRIGATED = "borewell_irrigated"  # Borewell / lift / micro-irrigation (drip/sprinkler)


class CropSeason(str, Enum):
    """Agricultural cropping season for semi-arid Deccan plateau."""

    KHARIF = "kharif"  # Monsoon (June - October)
    RABI = "rabi"  # Post-monsoon / Winter (October - February)
    SUMMER = "summer"  # Summer (February - May)


class RegionalSuitabilityTier(str, Enum):
    """Categorical suitability tier without arbitrary weight synthesis."""

    TIER_1_RECOMMENDED = "tier1_recommended"  # Highly recommended candidate crop for specified conditions
    TIER_2_CONDITIONAL = "tier2_conditional"  # Viable with specific soil, water, or drainage management
    TIER_3_INCOMPATIBLE = "tier3_incompatible"  # Incompatible due to fundamental ecological or agronomic constraint


class RegionalCropCandidate(BaseModel):
    """Structured evidence-based candidate crop from UAS Raichur & ICAR."""

    crop_key: str = Field(..., description="Standard lowercase crop identifier")
    display_name: str = Field(..., description="English common name")
    kannada_name: str = Field(..., description="Kannada script name and phonetic romanization")
    scientific_name: str = Field(..., description="Botanical binomial nomenclature")
    ecocrop_code: int = Field(..., description="FAO ECOCROP species code")
    suitability_tier: RegionalSuitabilityTier = Field(..., description="Categorical suitability tier")
    tier_label: str = Field(..., description="Farmer-friendly tier description")
    sowing_window: str = Field(..., description="Optimal sowing calendar period from UAS Raichur PoP")
    recommended_varieties: list[str] = Field(..., description="Certified varieties and hybrids released/recommended by UAS Raichur")
    soil_compatibility_note: str = Field(..., description="Field soil suitability and physical behavior explanation")
    water_management_note: str = Field(..., description="Irrigation requirement and moisture management context")
    agronomic_advice: list[str] = Field(default_factory=list, description="Actionable agronomic guidance from UAS Raichur PoP")
    provenance_sources: list[str] = Field(default_factory=list, description="Authoritative reference citations and source URLs")


class RegionalAdvisoryReport(BaseModel):
    """Consolidated regional agricultural candidates report for Raichur & Yadgir."""

    region_name: str = Field(default="Karnataka Zone 2 (North Eastern Dry Zone) & Zone 1 (NE Transition)")
    districts: list[str] = Field(default=["Raichur", "Yadgir"])
    field_soil_type: SoilType | None = Field(default=None, description="Farmer confirmed field soil type")
    irrigation_access: IrrigationStatus | None = Field(default=None, description="Farmer confirmed irrigation access")
    cropping_season: CropSeason | None = Field(default=None, description="Farmer confirmed cropping season")
    candidates: list[RegionalCropCandidate] = Field(..., description="Locally adapted staple crops evaluated under confirmed field parameters")
    context_notes: list[str] = Field(default_factory=list, description="Contextual agro-ecological and soil distribution notes")
