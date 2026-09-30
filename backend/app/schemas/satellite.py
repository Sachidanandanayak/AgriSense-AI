"""Pydantic schemas for satellite observation and vegetation indices serialization."""

from __future__ import annotations
from datetime import date
from typing import Any
from pydantic import BaseModel, Field, ConfigDict, model_validator


class IndexStatistics(BaseModel):
    """Zonal statistical aggregation across the circular analysis region."""

    min: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Minimum index value observed within the buffer region",
    )
    max: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Maximum index value observed within the buffer region",
    )
    mean: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Spatial mean index value within the buffer region",
    )
    median: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Spatial median index value within the buffer region",
    )
    std_dev: float | None = Field(
        default=None,
        ge=0.0,
        description="Spatial standard deviation of index values within the buffer region",
    )


class SatelliteResponse(BaseModel):
    """Normalized Sentinel-2 satellite observation and vegetation/water/moisture indices."""

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
    radius_m: float = Field(
        ...,
        gt=0.0,
        le=50000.0,
        description="Analysis radius in meters around the selected coordinate",
    )
    start_date: str = Field(
        ...,
        min_length=10,
        max_length=10,
        description="Start date of the observation window (YYYY-MM-DD)",
    )
    end_date: str = Field(
        ...,
        min_length=10,
        max_length=10,
        description="End date of the observation window (YYYY-MM-DD)",
    )
    usable_observations: int = Field(
        ...,
        ge=0,
        description="Number of usable Sentinel-2 scenes/observations in the composited window",
    )
    cloud_probability_threshold: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Pixel-level cloud probability cutoff percentage applied (0.0 to 100.0)",
    )
    ndvi_median: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Median Normalized Difference Vegetation Index (NDVI: (B8 - B4) / (B8 + B4))",
    )
    ndwi_median: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Median Normalized Difference Water Index (NDWI McFeeters 1996: (B3 - B8) / (B3 + B8))",
    )
    ndmi_median: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Median Normalized Difference Moisture Index (NDMI Gao 1996: (B8 - B11) / (B8 + B11))",
    )
    data_source: str = Field(
        default="Sentinel-2",
        description="Underlying satellite earth observation constellation",
    )
    statistics: dict[str, IndexStatistics] | None = Field(
        default=None,
        description="Detailed regional statistics (min, max, mean, median, std_dev) per index",
    )
    disclaimer: str = Field(
        default=(
            "The current implementation uses a point-centered analysis radius and therefore "
            "does not represent an exact farm boundary. Satellite indices are environmental "
            "indicators and are not direct crop-suitability scores."
        ),
        description="Scientific and architectural caveats regarding point-based analysis and interpretation",
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "SatelliteResponse":
        """Verify start_date is not after end_date."""
        try:
            d_start = date.fromisoformat(self.start_date)
            d_end = date.fromisoformat(self.end_date)
            if d_start > d_end:
                raise ValueError(
                    f"start_date ({self.start_date}) must be less than or equal to end_date ({self.end_date})"
                )
        except ValueError as exc:
            if "must be less than or equal to" in str(exc):
                raise
            raise ValueError(f"Invalid date format. Expected YYYY-MM-DD: {exc}") from exc
        return self

    def to_feature_dict(self) -> dict[str, float]:
        """Export normalized indices for future unified multi-source feature vector integration.

        Returns:
            Dictionary with ndvi_median, ndwi_median, and ndmi_median.
        """
        return {
            "satellite_ndvi_median": self.ndvi_median,
            "satellite_ndwi_median": self.ndwi_median,
            "satellite_ndmi_median": self.ndmi_median,
        }

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "latitude": 16.20,
                "longitude": 77.35,
                "radius_m": 500,
                "start_date": "2026-09-01",
                "end_date": "2026-09-25",
                "usable_observations": 3,
                "cloud_probability_threshold": 65,
                "ndvi_median": 0.54,
                "ndwi_median": 0.18,
                "ndmi_median": 0.31,
                "data_source": "Sentinel-2",
                "disclaimer": (
                    "The current implementation uses a point-centered analysis radius and therefore "
                    "does not represent an exact farm boundary. Satellite indices are environmental "
                    "indicators and are not direct crop-suitability scores."
                ),
            }
        }
    )
