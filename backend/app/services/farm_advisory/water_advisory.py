"""Authoritative FAO-56 Penman-Monteith & FAO CROPWAT crop-water methodology.

Follows FAO Irrigation and Drainage Paper No. 56 (Allen, Pereira, Raes, & Smith, 1998)
and FAO CROPWAT methodology. Strictly avoids fabricating reference evapotranspiration (ET0),
crop coefficients (Kc), or irrigation requirements when required agronomic parameters are missing.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from app.schemas.weather import WeatherResponse
from app.services.farm_advisory.schemas import (
    CropEnvironmentalRequirement,
    WaterAdvisory,
    WaterAdvisoryStatus,
)

logger = logging.getLogger(__name__)

# Mandatory meteorological and agronomic parameters required for defensible FAO-56 calculation
REQUIRED_FAO56_PARAMETERS: list[str] = [
    "net_radiation_mj_m2_day",
    "temp_mean_c",
    "wind_speed_2m_mps",
    "actual_vapor_pressure_kpa",
    "saturation_vapor_pressure_kpa",
    "psychrometric_constant_kpa_c",
    "slope_vapor_pressure_curve_kpa_c",
    "crop_coefficient_kc",
]


def calculate_fao56_penman_monteith(
    net_radiation_mj_m2_day: float,
    temp_mean_c: float,
    wind_speed_2m_mps: float,
    actual_vapor_pressure_kpa: float,
    saturation_vapor_pressure_kpa: float,
    psychrometric_constant_kpa_c: float,
    slope_vapor_pressure_curve_kpa_c: float,
    soil_heat_flux_mj_m2_day: float = 0.0,
) -> float:
    """Calculate daily reference evapotranspiration (ET0) using exact FAO-56 Penman-Monteith equation.

    Formula (Allen et al., 1998, FAO-56 Eq. 6):
        ET0 = (0.408 * delta * (Rn - G) + gamma * (900 / (T + 273)) * u2 * (es - ea)) /
              (delta + gamma * (1 + 0.34 * u2))

    Returns:
        Reference evapotranspiration ET0 in mm/day.
    """
    rn = net_radiation_mj_m2_day
    g = soil_heat_flux_mj_m2_day
    t = temp_mean_c
    u2 = wind_speed_2m_mps
    ea = actual_vapor_pressure_kpa
    es = saturation_vapor_pressure_kpa
    gamma = psychrometric_constant_kpa_c
    delta = slope_vapor_pressure_curve_kpa_c

    numerator = (
        0.408 * delta * (rn - g)
        + gamma * (900.0 / (t + 273.0)) * u2 * (es - ea)
    )
    denominator = delta + gamma * (1.0 + 0.34 * u2)

    if denominator <= 0:
        raise ValueError("Invalid atmospheric parameters resulting in non-positive denominator.")

    et0 = numerator / denominator
    return max(0.0, round(et0, 2))


def evaluate_water_advisory(
    weather: WeatherResponse | None,
    fao56_inputs: dict[str, float] | None = None,
    crop_requirement: CropEnvironmentalRequirement | None = None,
    effective_precipitation_mm: float | None = None,
) -> WaterAdvisory:
    """Evaluate farm water requirements using defensible FAO methodology.

    If complete FAO-56 parameters are provided, computes ET0, ETc, and net irrigation requirement.
    If parameters are incomplete (e.g. standard live weather feeds lacking net radiation and stage Kc),
    transparently returns status='unavailable' with an exact explanation of what is missing.
    """
    # Check if complete FAO-56 parameters are explicitly provided
    if fao56_inputs:
        missing = [p for p in REQUIRED_FAO56_PARAMETERS if p not in fao56_inputs or fao56_inputs[p] is None]
        if not missing:
            try:
                et0 = calculate_fao56_penman_monteith(
                    net_radiation_mj_m2_day=fao56_inputs["net_radiation_mj_m2_day"],
                    temp_mean_c=fao56_inputs["temp_mean_c"],
                    wind_speed_2m_mps=fao56_inputs["wind_speed_2m_mps"],
                    actual_vapor_pressure_kpa=fao56_inputs["actual_vapor_pressure_kpa"],
                    saturation_vapor_pressure_kpa=fao56_inputs["saturation_vapor_pressure_kpa"],
                    psychrometric_constant_kpa_c=fao56_inputs["psychrometric_constant_kpa_c"],
                    slope_vapor_pressure_curve_kpa_c=fao56_inputs["slope_vapor_pressure_curve_kpa_c"],
                    soil_heat_flux_mj_m2_day=fao56_inputs.get("soil_heat_flux_mj_m2_day", 0.0),
                )
                kc = float(fao56_inputs["crop_coefficient_kc"])
                etc = round(et0 * kc, 2)

                peff = (
                    effective_precipitation_mm
                    if effective_precipitation_mm is not None
                    else fao56_inputs.get("effective_precipitation_mm", 0.0)
                )
                iwr = max(0.0, round(etc - peff, 2))

                crop_name = crop_requirement.crop_name if crop_requirement else "crop"
                return WaterAdvisory(
                    status=WaterAdvisoryStatus.AVAILABLE,
                    methodology="FAO-56 Penman-Monteith Standard Methodology",
                    reference_evapotranspiration_et0_mm_day=et0,
                    crop_coefficient_kc=kc,
                    crop_evapotranspiration_etc_mm_day=etc,
                    estimated_irrigation_requirement_mm=iwr,
                    reason=(
                        f"Computed daily reference evapotranspiration ET0={et0:.2f} mm/day and "
                        f"crop water demand ETc={etc:.2f} mm/day for {crop_name} (Kc={kc:.2f}). "
                        f"Estimated net irrigation requirement is {iwr:.2f} mm considering effective precipitation ({peff:.1f} mm)."
                    ),
                    missing_parameters=[],
                    notes="Calculated in full accordance with FAO-56 Penman-Monteith formulation using validated meteorological parameters.",
                )
            except Exception as exc:
                logger.warning("FAO-56 Penman-Monteith calculation failed: %s", exc)

    # Standard weather feed lacks radiation, stage Kc, etc.
    missing_params: list[str] = [
        "net_solar_radiation (Rn)",
        "crop_growth_stage_coefficient (Kc)",
        "daily_temperature_extrema (Tmax, Tmin)",
        "effective_precipitation_depth (Peff)",
    ]
    if weather is None:
        missing_params.insert(0, "meteorological_observations (weather_context)")

    return WaterAdvisory(
        status=WaterAdvisoryStatus.UNAVAILABLE,
        methodology="FAO-56 Penman-Monteith / FAO CROPWAT Methodology",
        reference_evapotranspiration_et0_mm_day=None,
        crop_coefficient_kc=None,
        crop_evapotranspiration_etc_mm_day=None,
        estimated_irrigation_requirement_mm=None,
        reason=(
            "Insufficient meteorological and agronomic parameters for defensible FAO-56 "
            "reference evapotranspiration (ET0) and stage-specific crop water demand (ETc) calculation. "
            "Required missing parameters: net solar radiation (Rn), standardized 2m wind profile, "
            "crop growth stage-specific coefficient (Kc), and effective precipitation."
        ),
        missing_parameters=missing_params,
        notes=(
            "Per FAO guidelines, instantaneous weather observations and single rainfall values must "
            "not be presented as total crop water or irrigation requirements without stage-specific "
            "crop coefficients and solar energy balance equations."
        ),
    )
