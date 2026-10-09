"""Transparent environmental compatibility evaluation engine.

Implements deterministic evaluation of observed environmental variables against
authoritative FAO ECOCROP ecological thresholds. Follows the Sprengel-Liebig Law of
the Minimum (Hackett, 1991) to identify limiting agronomic factors without arbitrary
scoring formulas, synthetic percentages, or unverified weights.
"""

from __future__ import annotations

import logging
from typing import Any, Tuple

from app.services.farm_advisory.schemas import (
    CompatibilityStatus,
    CropEnvironmentalRequirement,
    VariableCompatibility,
)

logger = logging.getLogger(__name__)


def evaluate_numeric_range(
    variable_name: str,
    observed: float | None,
    unit: str,
    opt_min: float | None,
    opt_max: float | None,
    abs_min: float | None,
    abs_max: float | None,
    source_label: str = "FAO ECOCROP",
) -> VariableCompatibility:
    """Evaluate an observed continuous environmental metric against documented thresholds.

    Categorical Status Definitions:
    - 'favorable': Observed value falls entirely within the documented optimal range [opt_min, opt_max].
    - 'caution': Observed value is outside optimal boundaries, but remains within absolute survival/growth boundaries [abs_min, abs_max].
    - 'unfavorable': Observed value is strictly below abs_min or strictly above abs_max.
    - 'unavailable': Observed value or required source thresholds are missing/null.

    Args:
        variable_name: Friendly name of variable (e.g. 'Air Temperature', 'Rainfall', 'Soil pH').
        observed: Measured or estimated value.
        unit: Unit representation string (°C, mm, pH units).
        opt_min: Optimal lower bound.
        opt_max: Optimal upper bound.
        abs_min: Absolute minimum viable threshold.
        abs_max: Absolute maximum viable threshold.
        source_label: Attribution source label.

    Returns:
        Structured VariableCompatibility evaluation.
    """
    opt_str = (
        f"{opt_min:.1f} to {opt_max:.1f} {unit}"
        if opt_min is not None and opt_max is not None
        else "Not documented"
    )
    abs_str = (
        f"{abs_min:.1f} to {abs_max:.1f} {unit}"
        if abs_min is not None and abs_max is not None
        else "Not documented"
    )

    if observed is None:
        return VariableCompatibility(
            variable=variable_name,
            status=CompatibilityStatus.UNAVAILABLE,
            observed_value=None,
            observed_unit=unit,
            documented_optimal_range=opt_str,
            documented_absolute_range=abs_str,
            reason=f"Observed {variable_name.lower()} is unavailable in the supplied environmental context.",
            source=source_label,
        )

    if abs_min is None or abs_max is None:
        return VariableCompatibility(
            variable=variable_name,
            status=CompatibilityStatus.UNAVAILABLE,
            observed_value=observed,
            observed_unit=unit,
            documented_optimal_range=opt_str,
            documented_absolute_range=abs_str,
            reason=f"Authoritative {variable_name.lower()} requirements are unavailable in the {source_label} profile.",
            source=source_label,
        )

    # Check optimal range first (if documented)
    if opt_min is not None and opt_max is not None and opt_min <= observed <= opt_max:
        return VariableCompatibility(
            variable=variable_name,
            status=CompatibilityStatus.FAVORABLE,
            observed_value=observed,
            observed_unit=unit,
            documented_optimal_range=opt_str,
            documented_absolute_range=abs_str,
            reason=(
                f"Observed {variable_name.lower()} ({observed:.1f} {unit}) falls within "
                f"documented optimal range [{opt_str}]."
            ),
            source=source_label,
        )

    # Check absolute viable boundaries
    if abs_min <= observed <= abs_max:
        boundary_detail = (
            f"below optimal minimum ({opt_min:.1f} {unit})"
            if opt_min is not None and observed < opt_min
            else (
                f"above optimal maximum ({opt_max:.1f} {unit})"
                if opt_max is not None and observed > opt_max
                else "within documented tolerance"
            )
        )
        return VariableCompatibility(
            variable=variable_name,
            status=CompatibilityStatus.CAUTION,
            observed_value=observed,
            observed_unit=unit,
            documented_optimal_range=opt_str,
            documented_absolute_range=abs_str,
            reason=(
                f"Observed {variable_name.lower()} ({observed:.1f} {unit}) is {boundary_detail}, "
                f"but remains within absolute tolerance limits [{abs_str}]. Sub-optimal growth or stress possible."
            ),
            source=source_label,
        )

    # Outside absolute viable boundaries
    violation = "below absolute minimum" if observed < abs_min else "above absolute maximum"
    return VariableCompatibility(
        variable=variable_name,
        status=CompatibilityStatus.UNFAVORABLE,
        observed_value=observed,
        observed_unit=unit,
        documented_optimal_range=opt_str,
        documented_absolute_range=abs_str,
        reason=(
            f"Observed {variable_name.lower()} ({observed:.1f} {unit}) is {violation} "
            f"[{abs_str}]. High agronomic risk or physiological growth cessation."
        ),
        source=source_label,
    )


def classify_soil_texture_group(
    clay_pct: float | None,
    sand_pct: float | None,
    silt_pct: float | None,
) -> str | None:
    """Classify soil into broad physical texture groups (heavy, medium, light) following USDA / FAO taxonomy.

    - 'heavy': Clay-rich soils (clay >= 40%)
    - 'light': Coarse, sandy soils (sand >= 85%)
    - 'medium': Loams, silt loams, sandy clay loams, silty loams
    """
    if clay_pct is None or sand_pct is None:
        return None

    if clay_pct >= 40.0:
        return "heavy"
    if sand_pct >= 85.0:
        return "light"
    return "medium"


def evaluate_soil_texture(
    clay_pct: float | None,
    sand_pct: float | None,
    silt_pct: float | None,
    opt_textures: list[str] | None,
    abs_textures: list[str] | None,
    source_label: str = "FAO ECOCROP",
) -> VariableCompatibility:
    """Evaluate soil texture compatibility against documented FAO ECOCROP texture requirements."""
    opt_str = ", ".join(opt_textures) if opt_textures else "Not documented"
    abs_str = ", ".join(abs_textures) if abs_textures else "Not documented"

    classified_group = classify_soil_texture_group(clay_pct, sand_pct, silt_pct)

    if classified_group is None:
        return VariableCompatibility(
            variable="Soil Texture",
            status=CompatibilityStatus.UNAVAILABLE,
            observed_value=None,
            observed_unit="texture class",
            documented_optimal_range=opt_str,
            documented_absolute_range=abs_str,
            reason="Observed soil clay and sand fractions unavailable in digital soil context.",
            source=source_label,
        )

    if opt_textures is None and abs_textures is None:
        return VariableCompatibility(
            variable="Soil Texture",
            status=CompatibilityStatus.UNAVAILABLE,
            observed_value=classified_group,
            observed_unit="texture class",
            documented_optimal_range=opt_str,
            documented_absolute_range=abs_str,
            reason=f"Authoritative soil texture requirements are not documented in the {source_label} profile for this crop.",
            source=source_label,
        )

    norm_opts = [t.lower().strip() for t in (opt_textures or [])]
    norm_abs = [t.lower().strip() for t in (abs_textures or [])]

    # 'wide' in EcoCrop signifies wide texture adaptability
    if classified_group in norm_opts or "wide" in norm_opts:
        return VariableCompatibility(
            variable="Soil Texture",
            status=CompatibilityStatus.FAVORABLE,
            observed_value=f"{classified_group} (clay={clay_pct:.1f}%, sand={sand_pct:.1f}%)",
            observed_unit="texture class",
            documented_optimal_range=opt_str,
            documented_absolute_range=abs_str,
            reason=f"Classified soil texture '{classified_group}' matches documented optimal textures [{opt_str}].",
            source=source_label,
        )

    if classified_group in norm_abs or "wide" in norm_abs:
        return VariableCompatibility(
            variable="Soil Texture",
            status=CompatibilityStatus.CAUTION,
            observed_value=f"{classified_group} (clay={clay_pct:.1f}%, sand={sand_pct:.1f}%)",
            observed_unit="texture class",
            documented_optimal_range=opt_str,
            documented_absolute_range=abs_str,
            reason=(
                f"Classified soil texture '{classified_group}' is outside optimal textures [{opt_str}], "
                f"but within tolerable textures [{abs_str}]."
            ),
            source=source_label,
        )

    return VariableCompatibility(
        variable="Soil Texture",
        status=CompatibilityStatus.UNFAVORABLE,
        observed_value=f"{classified_group} (clay={clay_pct:.1f}%, sand={sand_pct:.1f}%)",
        observed_unit="texture class",
        documented_optimal_range=opt_str,
        documented_absolute_range=abs_str,
        reason=f"Classified soil texture '{classified_group}' is not documented as viable in [{abs_str}]. Potential drainage or root aeration restriction.",
        source=source_label,
    )


def evaluate_crop_environmental_compatibility(
    requirement: CropEnvironmentalRequirement | None,
    temperature_c: float | None,
    rainfall_mm: float | None,
    soil_ph: float | None,
    clay_pct: float | None = None,
    sand_pct: float | None = None,
    silt_pct: float | None = None,
) -> Tuple[CompatibilityStatus, dict[str, VariableCompatibility], list[str]]:
    """Perform multi-variable environmental compatibility evaluation for a candidate crop.

    Implements the Sprengel-Liebig Law of the Minimum:
    - If ANY factor is UNFAVORABLE -> overall compatibility is UNFAVORABLE.
    - Else if ANY factor is CAUTION -> overall compatibility is CAUTION.
    - Else if at least one factor is FAVORABLE (and none caution/unfavorable) -> FAVORABLE.
    - Else (if all factors UNAVAILABLE) -> UNAVAILABLE.

    Returns:
        Tuple of (overall_status, dict_of_variable_evaluations, list_of_risk_flags).
    """
    evaluations: dict[str, VariableCompatibility] = {}
    risk_flags: list[str] = []

    if requirement is None:
        risk_flags.append("crop_requirement_data_unavailable")
        return CompatibilityStatus.UNAVAILABLE, evaluations, risk_flags

    # 1. Temperature evaluation
    temp_eval = evaluate_numeric_range(
        variable_name="Temperature",
        observed=temperature_c,
        unit="°C",
        opt_min=requirement.temp_opt_min_c,
        opt_max=requirement.temp_opt_max_c,
        abs_min=requirement.temp_min_c,
        abs_max=requirement.temp_max_c,
    )
    evaluations["temperature"] = temp_eval
    if temp_eval.status in (CompatibilityStatus.CAUTION, CompatibilityStatus.UNFAVORABLE):
        risk_flags.append("temperature_outside_documented_range")

    # 2. Rainfall evaluation
    rain_eval = evaluate_numeric_range(
        variable_name="Rainfall",
        observed=rainfall_mm,
        unit="mm",
        opt_min=requirement.rainfall_opt_min_mm,
        opt_max=requirement.rainfall_opt_max_mm,
        abs_min=requirement.rainfall_min_mm,
        abs_max=requirement.rainfall_max_mm,
    )
    evaluations["rainfall"] = rain_eval
    if rain_eval.status in (CompatibilityStatus.CAUTION, CompatibilityStatus.UNFAVORABLE):
        risk_flags.append("rainfall_outside_documented_range")

    # 3. Soil pH evaluation
    ph_eval = evaluate_numeric_range(
        variable_name="Soil pH",
        observed=soil_ph,
        unit="pH",
        opt_min=requirement.soil_ph_opt_min,
        opt_max=requirement.soil_ph_opt_max,
        abs_min=requirement.soil_ph_min,
        abs_max=requirement.soil_ph_max,
    )
    evaluations["soil_ph"] = ph_eval
    if ph_eval.status in (CompatibilityStatus.CAUTION, CompatibilityStatus.UNFAVORABLE):
        risk_flags.append("soil_ph_outside_documented_range")

    # 4. Soil Texture evaluation
    tex_eval = evaluate_soil_texture(
        clay_pct=clay_pct,
        sand_pct=sand_pct,
        silt_pct=silt_pct,
        opt_textures=requirement.soil_textures_optimal,
        abs_textures=requirement.soil_textures_absolute,
    )
    evaluations["soil_texture"] = tex_eval
    if tex_eval.status == CompatibilityStatus.UNAVAILABLE:
        risk_flags.append("soil_texture_information_missing")
    elif tex_eval.status in (CompatibilityStatus.CAUTION, CompatibilityStatus.UNFAVORABLE):
        risk_flags.append("soil_texture_outside_documented_range")

    # Determine overall status via limiting factor principle
    statuses = [v.status for v in evaluations.values()]

    if CompatibilityStatus.UNFAVORABLE in statuses:
        overall = CompatibilityStatus.UNFAVORABLE
    elif CompatibilityStatus.CAUTION in statuses:
        overall = CompatibilityStatus.CAUTION
    elif any(s == CompatibilityStatus.FAVORABLE for s in statuses):
        overall = CompatibilityStatus.FAVORABLE
    else:
        overall = CompatibilityStatus.UNAVAILABLE

    return overall, evaluations, risk_flags
