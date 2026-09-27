"""Pydantic schemas for soil properties validation and response serialization."""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class SoilProperties(BaseModel):
    """Normalized agronomic soil physical and chemical properties in conventional units."""

    ph: float | None = Field(
        default=None,
        ge=0.0,
        le=14.0,
        description="Soil pH in H2O on standard 0-14 scale (SoilGrids mapped unit: pH*10, factor: 10)",
    )
    clay_pct: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Clay content percentage / g/100g (SoilGrids mapped unit: g/kg, factor: 10)",
    )
    sand_pct: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Sand content percentage / g/100g (SoilGrids mapped unit: g/kg, factor: 10)",
    )
    silt_pct: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Silt content percentage / g/100g (SoilGrids mapped unit: g/kg, factor: 10)",
    )
    organic_carbon_g_kg: float | None = Field(
        default=None,
        ge=0.0,
        description="Soil organic carbon in g/kg (SoilGrids mapped unit: dg/kg, factor: 10)",
    )
    bulk_density: float | None = Field(
        default=None,
        ge=0.0,
        description="Bulk density of the fine earth fraction in kg/dm³ (SoilGrids mapped unit: cg/cm³, factor: 100)",
    )
    cec: float | None = Field(
        default=None,
        ge=0.0,
        description="Cation Exchange Capacity at pH 7 in cmol(c)/kg (SoilGrids mapped unit: mmol(c)/kg, factor: 10)",
    )
    nitrogen_g_kg: float | None = Field(
        default=None,
        ge=0.0,
        description="Total nitrogen in g/kg (SoilGrids mapped unit: cg/kg, factor: 100)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ph": 7.2,
                "clay_pct": 42.1,
                "sand_pct": 19.4,
                "silt_pct": 38.5,
                "organic_carbon_g_kg": 12.1,
                "bulk_density": 1.63,
                "cec": 42.6,
                "nitrogen_g_kg": 1.34,
            }
        }
    )


class SoilResponse(BaseModel):
    """Normalized soil observation response schema for a geographic coordinate and depth interval."""

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees (-90.0 to 90.0)",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees (-180.0 to 180.0)",
    )
    depth_interval: str = Field(
        default="0-5cm",
        description="Standard depth interval (0-5cm, 5-15cm, 15-30cm, 30-60cm, 60-100cm, 100-200cm)",
    )
    soil: SoilProperties = Field(
        ...,
        description="Physical and chemical soil properties normalized to conventional agronomic units",
    )
    data_source: str = Field(
        default="ISRIC SoilGrids 2.0",
        description="Originating digital soil mapping dataset and provider",
    )
    resolution_m: int = Field(
        default=250,
        description="Spatial grid resolution of the soil predictions in meters (~250m)",
    )
    disclaimer: str = Field(
        default=(
            "SoilGrids predictions represent 250m resolution regional estimates and do not "
            "replace on-farm laboratory soil testing. Provided under CC BY 4.0 by ISRIC."
        ),
        description="Scientific caveats and licensing attribution",
    )

    def to_feature_dict(self) -> dict[str, float | None]:
        """Export normalized soil properties for future unified multi-source feature vector integration.

        Returns:
            Dictionary with soil property keys prefixed for model ingestion.
        """
        return {
            "soil_ph": self.soil.ph,
            "soil_clay_pct": self.soil.clay_pct,
            "soil_sand_pct": self.soil.sand_pct,
            "soil_silt_pct": self.soil.silt_pct,
            "soil_organic_carbon_g_kg": self.soil.organic_carbon_g_kg,
            "soil_bulk_density": self.soil.bulk_density,
            "soil_cec": self.soil.cec,
            "soil_nitrogen_g_kg": self.soil.nitrogen_g_kg,
        }

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "latitude": 20.59,
                "longitude": 78.96,
                "depth_interval": "0-5cm",
                "soil": {
                    "ph": 7.2,
                    "clay_pct": 42.1,
                    "sand_pct": 19.4,
                    "silt_pct": 38.5,
                    "organic_carbon_g_kg": 12.1,
                    "bulk_density": 1.63,
                    "cec": 42.6,
                    "nitrogen_g_kg": 1.34,
                },
                "data_source": "ISRIC SoilGrids 2.0",
                "resolution_m": 250,
                "disclaimer": (
                    "SoilGrids predictions represent 250m resolution regional estimates and do not "
                    "replace on-farm laboratory soil testing. Provided under CC BY 4.0 by ISRIC."
                ),
            }
        }
    )
