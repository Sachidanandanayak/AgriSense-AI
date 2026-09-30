"""Pydantic schemas and data contracts for Multi-Source Feature Engineering.

Defines the unified feature schema combining historical agricultural data, live weather
observations, Sentinel-2 satellite indices, and ISRIC SoilGrids properties into a normalized,
leakage-free, deterministic representation.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.services.feature_engineering.validators import (
    validate_coordinates,
    validate_no_target_leakage,
)

# Canonical list and ordering of ML input features (deterministic feature vector contract)
FEATURE_COLUMN_ORDER: list[str] = [
    # Historical / Agricultural features
    "nitrogen",
    "phosphorus",
    "potassium",
    "historical_temperature",
    "historical_humidity",
    "historical_ph",
    "historical_rainfall",
    # Derived agronomic ratios
    "n_p_ratio",
    "n_k_ratio",
    "p_k_ratio",
    # Weather features
    "weather_temperature",
    "weather_humidity",
    "weather_precipitation",
    "weather_wind_speed",
    # Satellite vegetation and moisture indices
    "satellite_ndvi",
    "satellite_ndwi",
    "satellite_ndmi",
    "satellite_usable_observations",
    "satellite_cloud_probability_threshold",
    # Soil physical and chemical properties
    "soil_ph",
    "soil_clay_pct",
    "soil_sand_pct",
    "soil_silt_pct",
    "soil_organic_carbon_g_kg",
    "soil_bulk_density",
    "soil_cec",
    "soil_nitrogen_g_kg",
]


class AlignmentMetadata(BaseModel):
    """Geospatial and temporal alignment metadata for an observation."""

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Observation latitude in WGS84 decimal degrees",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Observation longitude in WGS84 decimal degrees",
    )
    observation_date: str | None = Field(
        default=None,
        description="Target observation date in ISO format YYYY-MM-DD (e.g., planting or sampling date)",
    )
    location_source: str = Field(
        default="point_coordinate",
        description="Geospatial geometry representation (e.g. 'point_coordinate')",
    )
    temporal_window: str | None = Field(
        default=None,
        description="Analysis time horizon or temporal window descriptor",
    )
    data_sources: list[str] = Field(
        default_factory=list,
        description="List of originating data providers and constellations contributing to this record",
    )
    spatial_tolerance_deg: float = Field(
        default=0.005,
        description=(
            "Engineering spatial alignment tolerance applied in degrees (~0.005° ≈ 550m). "
            "Accommodates provider grid-centroid snapping and coordinate float precision. "
            "Does NOT represent cadastral farm-boundary equivalence."
        ),
    )
    spatial_assumptions: dict[str, str] = Field(
        default_factory=lambda: {
            "satellite": "Point-centered circular buffer (default 500m radius), not an exact farm polygon boundary.",
            "soil": "ISRIC SoilGrids 2.0 digital soil mapping predictions at 250m grid resolution, not an on-farm lab test.",
            "weather": "Open-Meteo atmospheric model grid interpolation for the requested coordinates.",
        },
        description="Explicit technical notes on spatial representations and approximations",
    )
    temporal_assumptions: dict[str, str] = Field(
        default_factory=lambda: {
            "satellite": "Aggregated temporal median over the specified cloud-filtered compositing window.",
            "soil": "Static spatial pedological reference for depth interval, not a daily dynamic observation.",
            "weather": "Instantaneous or forecast observation corresponding to the recorded timestamp.",
        },
        description="Explicit technical notes on temporal resolutions across sources",
    )
    disclaimer: str = Field(
        default=(
            "Multi-source features combine remote sensing, meteorological models, and spatial pedological "
            "grids. They represent environmental indicators for decision support, not certified lab assays."
        ),
        description="Architectural caveats and usage disclaimer",
    )



class AgriculturalFeatures(BaseModel):
    """Normalized soil nutrient and historical agronomic properties."""

    nitrogen: float | None = Field(
        default=None,
        ge=0.0,
        description="Available Nitrogen (N) content in soil (kg/ha)",
    )
    phosphorus: float | None = Field(
        default=None,
        ge=0.0,
        description="Available Phosphorus (P) content in soil (kg/ha)",
    )
    potassium: float | None = Field(
        default=None,
        ge=0.0,
        description="Available Potassium (K) content in soil (kg/ha)",
    )
    historical_temperature: float | None = Field(
        default=None,
        ge=-20.0,
        le=60.0,
        description="Historical seasonal mean temperature (°C) from baseline agricultural dataset",
    )
    historical_humidity: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Historical relative humidity (%) from baseline agricultural dataset",
    )
    historical_ph: float | None = Field(
        default=None,
        ge=0.0,
        le=14.0,
        description="Soil pH from agricultural measurements (0-14 scale)",
    )
    historical_rainfall: float | None = Field(
        default=None,
        ge=0.0,
        description="Historical seasonal rainfall in mm from baseline agricultural dataset",
    )


class WeatherFeatures(BaseModel):
    """Normalized live or historical meteorological observations."""

    weather_temperature: float | None = Field(
        default=None,
        ge=-100.0,
        le=70.0,
        description="Air temperature at 2m above ground in °C",
    )
    weather_humidity: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Relative humidity percentage (0.0 to 100.0)",
    )
    weather_precipitation: float | None = Field(
        default=None,
        ge=0.0,
        description="Rainfall / precipitation in millimeters",
    )
    weather_wind_speed: float | None = Field(
        default=None,
        ge=0.0,
        description="Wind speed at 10m above ground in meters per second",
    )
    weather_timestamp: str | None = Field(
        default=None,
        description="ISO 8601 timestamp of meteorological observation",
    )


class SatelliteFeatures(BaseModel):
    """Normalized Sentinel-2 satellite vegetation, water, and moisture indicators."""

    satellite_ndvi: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Median Normalized Difference Vegetation Index (NDVI)",
    )
    satellite_ndwi: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Median Normalized Difference Water Index (NDWI McFeeters 1996)",
    )
    satellite_ndmi: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Median Normalized Difference Moisture Index (NDMI Gao 1996)",
    )
    satellite_usable_observations: int | None = Field(
        default=None,
        ge=0,
        description="Count of usable Sentinel-2 scenes in the compositing window",
    )
    satellite_cloud_probability_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Pixel-level cloud probability cutoff percentage applied (0-100)",
    )
    satellite_start_date: str | None = Field(
        default=None,
        description="Observation window start date (YYYY-MM-DD)",
    )
    satellite_end_date: str | None = Field(
        default=None,
        description="Observation window end date (YYYY-MM-DD)",
    )
    satellite_radius_m: float | None = Field(
        default=None,
        gt=0.0,
        description="Zonal analysis radius in meters around the coordinate",
    )


class SoilFeatures(BaseModel):
    """Normalized ISRIC SoilGrids 2.0 digital soil mapping predictions."""

    soil_ph: float | None = Field(
        default=None,
        ge=0.0,
        le=14.0,
        description="Soil pH in H2O on standard 0-14 scale",
    )
    soil_clay_pct: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Clay content percentage (mass fraction g/100g)",
    )
    soil_sand_pct: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Sand content percentage (mass fraction g/100g)",
    )
    soil_silt_pct: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Silt content percentage (mass fraction g/100g)",
    )
    soil_organic_carbon_g_kg: float | None = Field(
        default=None,
        ge=0.0,
        description="Soil organic carbon in fine earth fraction (g/kg)",
    )
    soil_bulk_density: float | None = Field(
        default=None,
        ge=0.0,
        description="Bulk density of the fine earth fraction in kg/dm³",
    )
    soil_cec: float | None = Field(
        default=None,
        ge=0.0,
        description="Cation Exchange Capacity at pH 7 in cmol(c)/kg",
    )
    soil_nitrogen_g_kg: float | None = Field(
        default=None,
        ge=0.0,
        description="Total nitrogen in g/kg",
    )
    soil_depth_interval: str | None = Field(
        default=None,
        description="Depth interval represented (e.g. '0-5cm')",
    )
    soil_resolution_m: int | None = Field(
        default=None,
        description="Spatial grid resolution in meters (~250m)",
    )


class DerivedAgronomicFeatures(BaseModel):
    """Scientifically defensible domain-derived agronomic features."""

    n_p_ratio: float | None = Field(
        default=None,
        ge=0.0,
        description="Nitrogen to Phosphorus balance ratio (N/P). Undefined when P <= 0.",
    )
    n_k_ratio: float | None = Field(
        default=None,
        ge=0.0,
        description="Nitrogen to Potassium balance ratio (N/K). Undefined when K <= 0.",
    )
    p_k_ratio: float | None = Field(
        default=None,
        ge=0.0,
        description="Phosphorus to Potassium balance ratio (P/K). Undefined when K <= 0.",
    )


class MultiSourceObservation(BaseModel):
    """Unified multi-source observation combining agricultural, weather, satellite, and soil data."""

    # Alignment and Identity
    metadata: AlignmentMetadata = Field(
        ...,
        description="Spatial, temporal, and provenance metadata",
    )

    # Historical / Agricultural Features
    agricultural: AgriculturalFeatures = Field(
        default_factory=AgriculturalFeatures,
        description="Historical or measured agricultural nutrient and climate values",
    )

    # Weather Features
    weather: WeatherFeatures = Field(
        default_factory=WeatherFeatures,
        description="Normalized meteorological observations",
    )

    # Satellite Features
    satellite: SatelliteFeatures = Field(
        default_factory=SatelliteFeatures,
        description="Normalized Sentinel-2 vegetation and moisture indices",
    )

    # Soil Features
    soil: SoilFeatures = Field(
        default_factory=SoilFeatures,
        description="Normalized digital soil mapping properties",
    )

    # Derived Features
    derived: DerivedAgronomicFeatures = Field(
        default_factory=DerivedAgronomicFeatures,
        description="Scientifically derived nutrient balance ratios",
    )

    # Supervised Learning Target (Strictly separated from feature vectors)
    crop_label: str | None = Field(
        default=None,
        description="Ground-truth crop label for supervised training/evaluation. NEVER part of feature vector.",
    )

    @model_validator(mode="after")
    def validate_spatial_and_temporal_integrity(self) -> "MultiSourceObservation":
        """Verify internal consistency of coordinates and dates."""
        validate_coordinates(self.metadata.latitude, self.metadata.longitude)
        return self

    def to_feature_dict(
        self,
        include_target: bool = False,
        include_metadata: bool = False,
    ) -> dict[str, Any]:
        """Convert observation to a flat feature dictionary.

        By default, returns ONLY predictive features in a deterministic dictionary.
        Target labels and metadata are strictly excluded unless explicitly requested.

        Args:
            include_target: If True, includes 'target_crop_label' under an isolated target key.
            include_metadata: If True, includes geospatial and temporal metadata keys.

        Returns:
            Dictionary with feature values. Missing values are preserved as None.
        """
        features: dict[str, Any] = {
            # Agricultural
            "nitrogen": self.agricultural.nitrogen,
            "phosphorus": self.agricultural.phosphorus,
            "potassium": self.agricultural.potassium,
            "historical_temperature": self.agricultural.historical_temperature,
            "historical_humidity": self.agricultural.historical_humidity,
            "historical_ph": self.agricultural.historical_ph,
            "historical_rainfall": self.agricultural.historical_rainfall,
            # Derived ratios
            "n_p_ratio": self.derived.n_p_ratio,
            "n_k_ratio": self.derived.n_k_ratio,
            "p_k_ratio": self.derived.p_k_ratio,
            # Weather
            "weather_temperature": self.weather.weather_temperature,
            "weather_humidity": self.weather.weather_humidity,
            "weather_precipitation": self.weather.weather_precipitation,
            "weather_wind_speed": self.weather.weather_wind_speed,
            # Satellite
            "satellite_ndvi": self.satellite.satellite_ndvi,
            "satellite_ndwi": self.satellite.satellite_ndwi,
            "satellite_ndmi": self.satellite.satellite_ndmi,
            "satellite_usable_observations": self.satellite.satellite_usable_observations,
            "satellite_cloud_probability_threshold": self.satellite.satellite_cloud_probability_threshold,
            # Soil
            "soil_ph": self.soil.soil_ph,
            "soil_clay_pct": self.soil.soil_clay_pct,
            "soil_sand_pct": self.soil.soil_sand_pct,
            "soil_silt_pct": self.soil.soil_silt_pct,
            "soil_organic_carbon_g_kg": self.soil.soil_organic_carbon_g_kg,
            "soil_bulk_density": self.soil.soil_bulk_density,
            "soil_cec": self.soil.soil_cec,
            "soil_nitrogen_g_kg": self.soil.soil_nitrogen_g_kg,
        }

        # If not including target, ensure no target leakage occurs
        if not include_target:
            validate_no_target_leakage(features)
        else:
            features["target_crop_label"] = self.crop_label

        if include_metadata:
            features["meta_latitude"] = self.metadata.latitude
            features["meta_longitude"] = self.metadata.longitude
            features["meta_observation_date"] = self.metadata.observation_date
            features["meta_location_source"] = self.metadata.location_source
            features["meta_spatial_tolerance_deg"] = self.metadata.spatial_tolerance_deg
            features["meta_weather_timestamp"] = self.weather.weather_timestamp
            features["meta_satellite_start_date"] = self.satellite.satellite_start_date
            features["meta_satellite_end_date"] = self.satellite.satellite_end_date
            features["meta_satellite_radius_m"] = self.satellite.satellite_radius_m
            features["meta_soil_depth_interval"] = self.soil.soil_depth_interval
            features["meta_soil_resolution_m"] = self.soil.soil_resolution_m
            features["meta_data_sources"] = list(self.metadata.data_sources)


        return features

    def to_feature_vector(self) -> list[float | None]:
        """Generate deterministic ordered list of predictive feature values for ML inference.

        Returns:
            List of floats or None values matching FEATURE_COLUMN_ORDER.
            Zero metadata and zero target values are included.
        """
        feat_dict = self.to_feature_dict(include_target=False, include_metadata=False)
        return [feat_dict[col] for col in FEATURE_COLUMN_ORDER]

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "metadata": {
                    "latitude": 16.20,
                    "longitude": 77.35,
                    "observation_date": "2026-09-25",
                    "location_source": "point_coordinate",
                    "temporal_window": "2026-09-01_to_2026-09-25",
                    "data_sources": ["Open-Meteo", "Sentinel-2", "ISRIC SoilGrids 2.0"],
                },
                "agricultural": {
                    "nitrogen": 80.0,
                    "phosphorus": 40.0,
                    "potassium": 40.0,
                    "historical_temperature": None,
                    "historical_humidity": None,
                    "historical_ph": None,
                    "historical_rainfall": None,
                },
                "weather": {
                    "weather_temperature": 28.4,
                    "weather_humidity": 64.0,
                    "weather_precipitation": 0.0,
                    "weather_wind_speed": 3.2,
                    "weather_timestamp": "2026-09-25T17:15",
                },
                "satellite": {
                    "satellite_ndvi": 0.54,
                    "satellite_ndwi": 0.18,
                    "satellite_ndmi": 0.31,
                    "satellite_usable_observations": 3,
                    "satellite_cloud_probability_threshold": 65.0,
                    "satellite_start_date": "2026-09-01",
                    "satellite_end_date": "2026-09-25",
                    "satellite_radius_m": 500.0,
                },
                "soil": {
                    "soil_ph": 7.2,
                    "soil_clay_pct": 42.1,
                    "soil_sand_pct": 19.4,
                    "soil_silt_pct": 38.5,
                    "soil_organic_carbon_g_kg": 12.1,
                    "soil_bulk_density": 1.63,
                    "soil_cec": 42.6,
                    "soil_nitrogen_g_kg": 1.34,
                    "soil_depth_interval": "0-5cm",
                    "soil_resolution_m": 250,
                },
                "derived": {
                    "n_p_ratio": 2.0,
                    "n_k_ratio": 2.0,
                    "p_k_ratio": 1.0,
                },
                "crop_label": "rice",
            }
        },
    )


class MultiSourceFeatureVector(BaseModel):
    """Structured representation of extracted features ready for ML ingestion."""

    feature_names: list[str] = Field(
        default_factory=lambda: list(FEATURE_COLUMN_ORDER),
        description="Deterministic list of feature names matching feature_values order",
    )
    feature_values: list[float | None] = Field(
        ...,
        description="Ordered list of feature values corresponding to feature_names",
    )
    target: str | None = Field(
        default=None,
        description="Supervised crop label if provided for training/evaluation",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Geospatial, temporal, and provenance context",
    )
