"""Transparent agronomic explanation and limitations generator for Farm Advisory Engine."""

from __future__ import annotations

from typing import Sequence

from app.services.farm_advisory.schemas import (
    CompatibilityStatus,
    CropAdvisoryItem,
    DataQualityAudit,
    SatelliteEnvironmentalContext,
    WaterAdvisory,
    WaterAdvisoryStatus,
)


def generate_advisory_explanations(
    crop_advisories: Sequence[CropAdvisoryItem],
    water_advisory: WaterAdvisory,
    satellite_context: SatelliteEnvironmentalContext | None,
    data_quality: DataQualityAudit,
) -> list[str]:
    """Generate transparent, evidence-grounded agronomic explanations for farmer-facing reporting.

    Uses strictly scientific terminology:
    - 'compatibility'
    - 'documented environmental range'
    - 'benchmark-model confidence estimate'
    - 'environmental evidence'
    - 'advisory'
    - 'risk indicator'
    - 'source-backed requirement'

    Strictly avoids:
    - 'harvest success probability'
    - 'yield probability'
    - 'scientifically validated crop suitability percentage'
    - 'guaranteed crop recommendation'
    """
    explanations: list[str] = []

    # 1. Primary crop recommendation and confidence estimate
    if crop_advisories:
        top = crop_advisories[0]
        explanations.append(
            f"The benchmark machine learning model identified '{top.crop}' as the top-ranked candidate "
            f"with a benchmark-model confidence estimate of {top.confidence_percentage}."
        )

        # Describe overall compatibility and key limiting factors
        compat_text = top.overall_compatibility.value
        explanations.append(
            f"Authoritative environmental evaluation against FAO ECOCROP ecological thresholds classifies "
            f"'{top.crop}' as '{compat_text}' overall."
        )

        # Highlight variable-specific evaluations for the top crop
        for var_name, eval_item in top.compatibility_evaluations.items():
            if eval_item.status != CompatibilityStatus.UNAVAILABLE:
                explanations.append(f"{eval_item.variable}: {eval_item.reason}")

        # List alternatives
        if len(crop_advisories) > 1:
            alt_summaries = [
                f"'{c.crop}' (model confidence: {c.confidence_percentage}, compatibility: {c.overall_compatibility.value})"
                for c in crop_advisories[1:]
            ]
            explanations.append(
                f"Secondary candidate crops evaluated: {'; '.join(alt_summaries)}."
            )

    # 2. Risk flags explanation
    if data_quality.risk_flags:
        formatted_flags = ", ".join(f"'{f}'" for f in data_quality.risk_flags)
        explanations.append(
            f"Agronomic risk indicators identified: {formatted_flags}. "
            f"Refer to individual variable evaluations and advisory notes for mitigation context."
        )

    # 3. Satellite environmental context explanation
    if satellite_context and satellite_context.available:
        explanations.append(
            f"Sentinel-2 remote sensing ({satellite_context.observation_window or 'recent window'}) "
            f"indicates median NDVI={satellite_context.ndvi_median if satellite_context.ndvi_median is not None else 'N/A'}, "
            f"NDWI={satellite_context.ndwi_median if satellite_context.ndwi_median is not None else 'N/A'}, and "
            f"NDMI={satellite_context.ndmi_median if satellite_context.ndmi_median is not None else 'N/A'}. "
            f"These metrics reflect current vegetative greenness and moisture context, not direct suitability proof."
        )

    # 4. Water advisory explanation
    if water_advisory.status == WaterAdvisoryStatus.AVAILABLE:
        explanations.append(
            f"Water requirement advisory: {water_advisory.reason}"
        )
    else:
        explanations.append(
            f"Water requirement advisory status is 'unavailable': {water_advisory.reason}"
        )

    return explanations


def generate_advisory_limitations(
    crop_advisories: Sequence[CropAdvisoryItem],
    data_quality: DataQualityAudit,
) -> list[str]:
    """Generate explicit scientific caveats, model boundaries, and operational limitations."""
    limitations: list[str] = [
        (
            "Benchmark Model Scope: The crop recommendation engine employs a benchmark classifier "
            "trained on controlled trial data (2,200 samples). Its probability estimate reflects "
            "statistical likelihood within training feature boundaries and does NOT constitute "
            "a scientifically validated crop-suitability, commercial yield, or harvest-success model."
        ),
        (
            "Authoritative Agro-Ecological Baselines: Compatibility statuses are grounded strictly "
            "in FAO ECOCROP macro-scale ecological requirements. Macro-scale ranges do not reflect "
            "local microclimates, cold-air drainages, slope aspects, or proprietary cultivar tolerances."
        ),
        (
            "Environmental Context Indicators: Sentinel-2 satellite indices (NDVI, NDWI, NDMI) and "
            "meteorological feeds provide contextual environmental monitoring. Remote sensing observations "
            "alone do not prove crop suitability or disease immunity."
        ),
        (
            "Digital Soil Mapping Spatial Scale: ISRIC SoilGrids 2.0 properties represent 250m grid-scale "
            "spatial statistical predictions. They provide regional reference values and do not replace "
            "certified on-farm laboratory chemical soil analyses."
        ),
        (
            "Crop Water Requirement Limitations: In accordance with FAO-56 Penman-Monteith methodology, "
            "defensible irrigation requirements necessitate net solar radiation, daily temperature extrema, "
            "standardized wind measurements, and stage-specific crop coefficients (Kc). Instantaneous weather "
            "readings must not be interpreted as seasonal irrigation requirements."
        ),
        (
            "Unmodelled Agronomic Risks: Field management factors such as pest and disease outbreaks, "
            "weed pressure, frost events, hail damage, drainage tile infrastructure, seed variety differences, "
            "and commodity market volatility are not modeled by this advisory engine."
        ),
    ]

    # Add context-specific missing-data limitations
    if data_quality.missing_sources:
        missing_str = ", ".join(data_quality.missing_sources)
        limitations.append(
            f"Data Source Incompleteness: Environmental data was unavailable for [{missing_str}]. "
            f"Advisory evaluations for these dimensions were set to 'unavailable' rather than imputed."
        )

    if data_quality.stale_sources:
        stale_str = ", ".join(data_quality.stale_sources)
        limitations.append(
            f"Data Staleness Notice: Environmental context for [{stale_str}] exceeded operational freshness "
            f"windows relative to the target observation date."
        )

    return limitations
