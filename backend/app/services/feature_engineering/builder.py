"""Feature builder and pipeline orchestration for multi-source feature engineering.

Responsible for spatial/temporal alignment, feature normalization, safe feature derivation,
and unified feature vector construction.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.schemas.weather import WeatherResponse
from app.schemas.satellite import SatelliteResponse
from app.schemas.soil import SoilResponse
from app.core.config import settings
from app.services.feature_engineering.schemas import (
    FEATURE_COLUMN_ORDER,
    AlignmentMetadata,
    AgriculturalFeatures,
    WeatherFeatures,
    SatelliteFeatures,
    SoilFeatures,
    DerivedAgronomicFeatures,
    MultiSourceObservation,
    MultiSourceFeatureVector,
)
from app.services.feature_engineering.normalizer import (
    normalize_weather_response,
    normalize_satellite_response,
    normalize_soil_response,
    normalize_agricultural_data,
)
from app.services.feature_engineering.validators import (
    validate_coordinates,
    validate_cross_source_spatial_alignment,
    validate_satellite_date_window,
    validate_temporal_alignment,
    validate_no_target_leakage,
    safe_ratio,
    parse_iso_date,
    SpatialAlignmentError,
    TemporalAlignmentError,
)


class MultiSourceFeatureBuilder:
    """Builder class orchestrating multi-source ingestion, alignment, and feature creation."""

    def __init__(
        self,
        spatial_tolerance_deg: float | None = None,
        satellite_max_window_days: int | None = None,
        weather_max_gap_days: int | None = None,
    ) -> None:
        """Initialize builder.

        Args:
            spatial_tolerance_deg: Maximum allowable difference in coordinates between
                independent source observations (defaults to settings.FEATURE_SPATIAL_TOLERANCE_DEG, ~0.005° ≈ 550m).
            satellite_max_window_days: Maximum allowable gap in days between satellite window end and observation date
                (defaults to settings.FEATURE_SATELLITE_MAX_WINDOW_DAYS, 14 days).
            weather_max_gap_days: Maximum allowable disparity in days between observation date and weather
                (defaults to settings.FEATURE_WEATHER_MAX_GAP_DAYS, 7 days).
        """
        self.spatial_tolerance_deg = (
            spatial_tolerance_deg
            if spatial_tolerance_deg is not None
            else settings.FEATURE_SPATIAL_TOLERANCE_DEG
        )
        self.satellite_max_window_days = (
            satellite_max_window_days
            if satellite_max_window_days is not None
            else settings.FEATURE_SATELLITE_MAX_WINDOW_DAYS
        )
        self.weather_max_gap_days = (
            weather_max_gap_days
            if weather_max_gap_days is not None
            else settings.FEATURE_WEATHER_MAX_GAP_DAYS
        )

    def derive_agronomic_features(
        self,
        agri: AgriculturalFeatures,
    ) -> DerivedAgronomicFeatures:
        """Derive scientifically defensible nutrient ratios from agricultural features.

        Ratios:
            - n_p_ratio: Nitrogen / Phosphorus
            - n_k_ratio: Nitrogen / Potassium
            - p_k_ratio: Phosphorus / Potassium

        Ratios are strictly computed only when the denominator is strictly positive (> 0.0).
        Zero or missing denominators evaluate to None without error or synthetic substitution.

        Args:
            agri: Normalized AgriculturalFeatures.

        Returns:
            DerivedAgronomicFeatures instance.
        """
        return DerivedAgronomicFeatures(
            n_p_ratio=safe_ratio(agri.nitrogen, agri.phosphorus),
            n_k_ratio=safe_ratio(agri.nitrogen, agri.potassium),
            p_k_ratio=safe_ratio(agri.phosphorus, agri.potassium),
        )

    def build_unified_observation(
        self,
        latitude: float,
        longitude: float,
        observation_date: str | date | None = None,
        weather: WeatherResponse | dict[str, Any] | None = None,
        satellite: SatelliteResponse | dict[str, Any] | None = None,
        soil: SoilResponse | dict[str, Any] | None = None,
        agricultural_data: dict[str, Any] | None = None,
        crop_label: str | None = None,
        location_source: str = "point_coordinate",
        temporal_window: str | None = None,
        strict_spatial: bool = True,
        strict_temporal: bool = True,
        spatial_tolerance_deg: float | None = None,
        satellite_max_window_days: int | None = None,
        weather_max_gap_days: int | None = None,
    ) -> MultiSourceObservation:
        """Construct a unified multi-source observation with validation and alignment.

        Args:
            latitude: Target latitude in WGS84 decimal degrees [-90, 90].
            longitude: Target longitude in WGS84 decimal degrees [-180, 180].
            observation_date: Optional target observation date (YYYY-MM-DD).
            weather: WeatherResponse or dict from weather service.
            satellite: SatelliteResponse or dict from satellite service.
            soil: SoilResponse or dict from soil service.
            agricultural_data: Optional dictionary containing agricultural nutrient data.
            crop_label: Supervised crop target label (isolated from prediction features).
            location_source: Representation tag for geometry (default: 'point_coordinate').
            temporal_window: Optional descriptor of the temporal analysis window.
            strict_spatial: When True, enforces that source coordinates match target coordinates.
            strict_temporal: When True, validates temporal coherence between observation date and sources.
            spatial_tolerance_deg: Optional call-time override for spatial tolerance.
            satellite_max_window_days: Optional call-time override for satellite temporal window margin.
            weather_max_gap_days: Optional call-time override for weather temporal gap margin.

        Returns:
            MultiSourceObservation containing normalized and derived features.

        Raises:
            SpatialAlignmentError: If coordinates are out of bounds or cross-source coordinates mismatch.
            TemporalAlignmentError: If date windows or temporal coherence fail validation.
        """
        # Resolve effective tolerances
        effective_spatial_tol = (
            spatial_tolerance_deg
            if spatial_tolerance_deg is not None
            else self.spatial_tolerance_deg
        )
        effective_sat_margin = (
            satellite_max_window_days
            if satellite_max_window_days is not None
            else self.satellite_max_window_days
        )
        effective_weather_gap = (
            weather_max_gap_days
            if weather_max_gap_days is not None
            else self.weather_max_gap_days
        )

        # 1. Validate primary target coordinates
        val_lat, val_lon = validate_coordinates(latitude, longitude)

        # 2. Validate cross-source spatial alignment
        if strict_spatial:
            if weather is not None:
                w_lat = getattr(weather, "latitude", None) or (
                    weather.get("latitude") if isinstance(weather, dict) else None
                )
                w_lon = getattr(weather, "longitude", None) or (
                    weather.get("longitude") if isinstance(weather, dict) else None
                )
                validate_cross_source_spatial_alignment(
                    val_lat, val_lon, "Weather", w_lat, w_lon, effective_spatial_tol
                )

            if satellite is not None:
                s_lat = getattr(satellite, "latitude", None) or (
                    satellite.get("latitude") if isinstance(satellite, dict) else None
                )
                s_lon = getattr(satellite, "longitude", None) or (
                    satellite.get("longitude") if isinstance(satellite, dict) else None
                )
                validate_cross_source_spatial_alignment(
                    val_lat, val_lon, "Satellite", s_lat, s_lon, effective_spatial_tol
                )

            if soil is not None:
                so_lat = getattr(soil, "latitude", None) or (
                    soil.get("latitude") if isinstance(soil, dict) else None
                )
                so_lon = getattr(soil, "longitude", None) or (
                    soil.get("longitude") if isinstance(soil, dict) else None
                )
                validate_cross_source_spatial_alignment(
                    val_lat, val_lon, "Soil", so_lat, so_lon, effective_spatial_tol
                )

        # 3. Validate temporal alignment
        sat_start: str | None = None
        sat_end: str | None = None
        if satellite is not None:
            sat_start = getattr(satellite, "start_date", None) or (
                satellite.get("start_date") if isinstance(satellite, dict) else None
            )
            sat_end = getattr(satellite, "end_date", None) or (
                satellite.get("end_date") if isinstance(satellite, dict) else None
            )
            if sat_start and sat_end:
                validate_satellite_date_window(sat_start, sat_end)

        w_timestamp: str | None = None
        if weather is not None:
            w_timestamp = getattr(weather, "weather_timestamp", None) or (
                weather.get("weather_timestamp") if isinstance(weather, dict) else None
            )

        if strict_temporal and observation_date:
            validate_temporal_alignment(
                observation_date=observation_date,
                satellite_start_date=sat_start,
                satellite_end_date=sat_end,
                weather_timestamp=w_timestamp,
                satellite_max_window_days=effective_sat_margin,
                max_weather_gap_days=effective_weather_gap,
            )


        # 4. Normalize source representations
        weather_feat = normalize_weather_response(weather)
        satellite_feat = normalize_satellite_response(satellite)
        soil_feat = normalize_soil_response(soil)
        agri_feat = normalize_agricultural_data(agricultural_data)

        # 5. Derive agronomic ratios
        derived_feat = self.derive_agronomic_features(agri_feat)

        # 6. Extract supervised crop label if provided in agricultural data dict
        resolved_crop_label = crop_label
        if resolved_crop_label is None and agricultural_data and "label" in agricultural_data:
            resolved_crop_label = str(agricultural_data["label"])

        # 7. Collect provenance data sources
        data_sources: list[str] = []
        if agricultural_data is not None:
            data_sources.append("Historical Agricultural Dataset")
        if weather is not None:
            data_sources.append("Open-Meteo Weather")
        if satellite is not None:
            data_sources.append("Sentinel-2 MSI")
        if soil is not None:
            data_sources.append("ISRIC SoilGrids 2.0")

        # 8. Determine observation date string
        obs_date_str = str(parse_iso_date(observation_date)) if observation_date else None

        # Determine default temporal window descriptor if not specified
        if temporal_window is None:
            if sat_start and sat_end:
                temporal_window = f"{sat_start}_to_{sat_end}"
            elif obs_date_str:
                temporal_window = obs_date_str

        metadata = AlignmentMetadata(
            latitude=val_lat,
            longitude=val_lon,
            observation_date=obs_date_str,
            location_source=location_source,
            temporal_window=temporal_window,
            data_sources=data_sources,
            spatial_tolerance_deg=effective_spatial_tol,
        )


        return MultiSourceObservation(
            metadata=metadata,
            agricultural=agri_feat,
            weather=weather_feat,
            satellite=satellite_feat,
            soil=soil_feat,
            derived=derived_feat,
            crop_label=resolved_crop_label,
        )

    def to_feature_vector(self, observation: MultiSourceObservation) -> list[float | None]:
        """Convert a MultiSourceObservation into a deterministic ordered feature vector.

        Guarantees that target labels and metadata are excluded from the output.

        Args:
            observation: MultiSourceObservation instance.

        Returns:
            Deterministic list of feature values corresponding to FEATURE_COLUMN_ORDER.
        """
        return observation.to_feature_vector()

    def to_feature_dict(
        self,
        observation: MultiSourceObservation,
        include_target: bool = False,
        include_metadata: bool = False,
    ) -> dict[str, Any]:
        """Export observation to feature dictionary.

        Args:
            observation: MultiSourceObservation instance.
            include_target: Include target_crop_label if True.
            include_metadata: Include meta_* fields if True.

        Returns:
            Dictionary with feature values.
        """
        return observation.to_feature_dict(
            include_target=include_target,
            include_metadata=include_metadata,
        )

    def create_feature_vector_record(
        self,
        observation: MultiSourceObservation,
    ) -> MultiSourceFeatureVector:
        """Create structured MultiSourceFeatureVector record ready for ML ingestion.

        Args:
            observation: MultiSourceObservation instance.

        Returns:
            MultiSourceFeatureVector separating feature vector, target, and metadata.
        """
        return MultiSourceFeatureVector(
            feature_names=list(FEATURE_COLUMN_ORDER),
            feature_values=observation.to_feature_vector(),
            target=observation.crop_label,
            metadata=observation.metadata.model_dump(),
        )

    @staticmethod
    def get_feature_names() -> list[str]:
        """Return the canonical ordered list of feature column names."""
        return list(FEATURE_COLUMN_ORDER)


# Global default builder instance
feature_builder = MultiSourceFeatureBuilder()
