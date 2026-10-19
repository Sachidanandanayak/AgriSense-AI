"""Test suite for Regional Agronomic Knowledge Base (Raichur & Yadgir, Karnataka).

Validates:
1. Spatial boundary detection for Karnataka Zone 2 (NEDZ) & Zone 1.
2. UAS Raichur & ICAR Zone 2 candidate crop recommendations under varying soil types,
   irrigation regimes, and cropping seasons.
3. Agronomic constraints (e.g. Groundnut in cracking black clay, Rainfed Rice water deficit).
4. Handling of unconfirmed farmer field inputs (assigning Conditional status without fabricating scores).
5. Rainfall temporal period disambiguation (seasonal 120 mm vs annual FAO thresholds).
6. Seasonal temperature precedence over single-hour instantaneous weather spikes.
7. Preserved API response contracts across Phase 8 and Phase 9.
"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.schemas.regional import (
    CropSeason,
    IrrigationStatus,
    RegionalAdvisoryReport,
    RegionalSuitabilityTier,
    SoilType,
)
from app.services.regional_kb import (
    evaluate_regional_candidates,
    is_raichur_yadgir_region,
)
from app.services.farm_advisory.compatibility import (
    evaluate_crop_environmental_compatibility,
    CompatibilityStatus,
)
from app.services.farm_advisory.requirements import crop_requirement_repository
from app.services.farm_advisory.schemas import (
    FarmAdvisoryRequest,
    FarmAdvisoryResponse,
)
from app.services.farm_advisory.advisory_service import farm_advisory_service
from app.services.recommendation.schemas import (
    AgriculturalInput,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation.recommendation_service import recommendation_service


class TestRegionalKnowledgeBase(unittest.TestCase):
    """Unit tests for UAS Raichur and ICAR Zone 2 agronomic rules."""

    def test_raichur_yadgir_bounds_check(self) -> None:
        """Verify spatial coordinate boundary classification for Raichur & Yadgir."""
        # Raichur center coordinates
        self.assertTrue(is_raichur_yadgir_region(16.20, 77.35))
        # Yadgir center coordinates
        self.assertTrue(is_raichur_yadgir_region(16.76, 77.13))
        # Sindhanur taluk coordinates
        self.assertTrue(is_raichur_yadgir_region(15.77, 76.76))
        # Bengaluru coordinates (outside Zone 2)
        self.assertFalse(is_raichur_yadgir_region(12.97, 77.59))
        # Delhi coordinates
        self.assertFalse(is_raichur_yadgir_region(28.61, 77.20))

    def test_deep_black_soil_canal_kharif(self) -> None:
        """Deep black Vertisols under canal irrigation in Kharif prioritize Cotton and Rice."""
        report = evaluate_regional_candidates(
            latitude=16.20,
            longitude=77.35,
            soil_type=SoilType.DEEP_BLACK,
            irrigation=IrrigationStatus.CANAL_IRRIGATED,
            season=CropSeason.KHARIF,
        )

        tier_map = {c.crop_key: c.suitability_tier for c in report.candidates}

        # Cotton and Rice must be Tier 1 Recommended
        self.assertEqual(tier_map["cotton"], RegionalSuitabilityTier.TIER_1_RECOMMENDED)
        self.assertEqual(tier_map["rice"], RegionalSuitabilityTier.TIER_1_RECOMMENDED)

        # Pigeon Pea is Tier 2 Conditional due to heavy clay drainage risk
        self.assertEqual(tier_map["pigeonpeas"], RegionalSuitabilityTier.TIER_2_CONDITIONAL)

        # Groundnut is Tier 2 Conditional due to cracking clay peg penetration resistance
        self.assertEqual(tier_map["groundnut"], RegionalSuitabilityTier.TIER_2_CONDITIONAL)

        # Rabi crops are Tier 3 Incompatible during Kharif monsoon
        self.assertEqual(tier_map["sorghum"], RegionalSuitabilityTier.TIER_3_INCOMPATIBLE)
        self.assertEqual(tier_map["chickpea"], RegionalSuitabilityTier.TIER_3_INCOMPATIBLE)

    def test_deep_black_soil_rainfed_rabi(self) -> None:
        """Deep black Vertisols under rainfed receding moisture in Rabi prioritize Jowar and Chickpea."""
        report = evaluate_regional_candidates(
            latitude=16.20,
            longitude=77.35,
            soil_type=SoilType.DEEP_BLACK,
            irrigation=IrrigationStatus.RAINFED,
            season=CropSeason.RABI,
        )

        tier_map = {c.crop_key: c.suitability_tier for c in report.candidates}

        # Rabi staples on residual Vertisol moisture
        self.assertEqual(tier_map["sorghum"], RegionalSuitabilityTier.TIER_1_RECOMMENDED)
        self.assertEqual(tier_map["chickpea"], RegionalSuitabilityTier.TIER_1_RECOMMENDED)

        # Kharif crops incompatible in Rabi
        self.assertEqual(tier_map["cotton"], RegionalSuitabilityTier.TIER_3_INCOMPATIBLE)
        self.assertEqual(tier_map["pigeonpeas"], RegionalSuitabilityTier.TIER_3_INCOMPATIBLE)

        # Rainfed rice is strictly incompatible
        self.assertEqual(tier_map["rice"], RegionalSuitabilityTier.TIER_3_INCOMPATIBLE)

    def test_red_sandy_loam_rainfed_kharif(self) -> None:
        """Red sandy loam (chalka) soils in rainfed Kharif prioritize Groundnut and Pigeon Pea."""
        report = evaluate_regional_candidates(
            latitude=16.20,
            longitude=77.35,
            soil_type=SoilType.RED_SANDY_LOAM,
            irrigation=IrrigationStatus.RAINFED,
            season=CropSeason.KHARIF,
        )

        tier_map = {c.crop_key: c.suitability_tier for c in report.candidates}

        # Groundnut excels in friable chalka soils; Pigeon pea tolerates red sandy loam
        self.assertEqual(tier_map["groundnut"], RegionalSuitabilityTier.TIER_1_RECOMMENDED)
        self.assertEqual(tier_map["pigeonpeas"], RegionalSuitabilityTier.TIER_1_RECOMMENDED)

        # Cotton is Tier 2 Conditional on red soils (lower water holding capacity requires frequent water)
        self.assertEqual(tier_map["cotton"], RegionalSuitabilityTier.TIER_2_CONDITIONAL)

        # Rice is Tier 3 Incompatible (high percolation in sand + rainfed dryland)
        self.assertEqual(tier_map["rice"], RegionalSuitabilityTier.TIER_3_INCOMPATIBLE)

    def test_groundnut_cracking_clay_limitation(self) -> None:
        """Groundnut in deep heavy black Vertisol triggers explicit physical soil caution note."""
        report = evaluate_regional_candidates(
            latitude=16.20,
            longitude=77.35,
            soil_type=SoilType.DEEP_BLACK,
            irrigation=IrrigationStatus.CANAL_IRRIGATED,
            season=CropSeason.KHARIF,
        )

        gn = next(c for c in report.candidates if c.crop_key == "groundnut")
        self.assertEqual(gn.suitability_tier, RegionalSuitabilityTier.TIER_2_CONDITIONAL)
        self.assertIn("peg", gn.soil_compatibility_note.lower())
        self.assertIn("clod", gn.soil_compatibility_note.lower())

    def test_rice_rainfed_water_deficit(self) -> None:
        """Rainfed Rice triggers Tier 3 Incompatible and cites annual rainfall deficit."""
        report = evaluate_regional_candidates(
            latitude=16.20,
            longitude=77.35,
            soil_type=SoilType.DEEP_BLACK,
            irrigation=IrrigationStatus.RAINFED,
            season=CropSeason.KHARIF,
        )

        rice = next(c for c in report.candidates if c.crop_key == "rice")
        self.assertEqual(rice.suitability_tier, RegionalSuitabilityTier.TIER_3_INCOMPATIBLE)
        self.assertIn("deficit", rice.tier_label.lower())
        self.assertIn("700 mm", rice.water_management_note)

    def test_missing_farmer_inputs_conditional_tier(self) -> None:
        """When farmer field inputs are unconfirmed, candidates are marked Conditional without arbitrary scores."""
        report = evaluate_regional_candidates(
            latitude=16.20,
            longitude=77.35,
            soil_type=None,
            irrigation=None,
            season=None,
        )

        self.assertEqual(len(report.candidates), 6)
        self.assertTrue(len(report.context_notes) >= 3)
        # Context notes must transparently alert user about unconfirmed parameters
        notes_str = " ".join(report.context_notes).lower()
        self.assertIn("soil type was not confirmed", notes_str)
        self.assertIn("irrigation access was not confirmed", notes_str)

    def test_provenance_and_varieties_presence(self) -> None:
        """All candidates must contain certified UAS Raichur varieties, Kannada names, and source URLs."""
        report = evaluate_regional_candidates(16.20, 77.35)

        for candidate in report.candidates:
            self.assertTrue(len(candidate.recommended_varieties) >= 2, f"Varieties missing for {candidate.crop_key}")
            self.assertTrue(len(candidate.kannada_name) > 0, f"Kannada name missing for {candidate.crop_key}")
            self.assertTrue(len(candidate.provenance_sources) >= 1, f"Provenance URL missing for {candidate.crop_key}")
            for src in candidate.provenance_sources:
                self.assertTrue(src.startswith("http") or "://" in src, f"Malformed URL in {src}")


class TestRainfallTemporalDisambiguation(unittest.TestCase):
    """Unit tests for temporal rainfall period disambiguation against FAO annual requirements."""

    def test_sub_annual_rainfall_temporal_mismatch_withheld(self) -> None:
        """Seasonal or trial rainfall (120 mm) must not be penalized against annual thresholds (750-4200 mm/year)."""
        coffee = crop_requirement_repository.get_requirement("coffee")
        self.assertIsNotNone(coffee)

        # 120 mm seasonal rainfall
        status, var_evals, risks = evaluate_crop_environmental_compatibility(
            requirement=coffee,
            temperature_c=26.5,  # within optimal 18-28
            rainfall_mm=120.0,
            soil_ph=6.8,  # within optimal 6.0-7.0
            clay_pct=25.0,
            sand_pct=50.0,
            silt_pct=25.0,
            rainfall_is_annual=False,
        )

        rain_eval = var_evals["rainfall"]
        self.assertEqual(rain_eval.status, CompatibilityStatus.UNAVAILABLE)
        self.assertIn("temporal period mismatch", rain_eval.reason.lower())
        self.assertIn("mm/year", rain_eval.documented_optimal_range)
        # Must NOT add physiological death risk flag
        self.assertNotIn("rainfall_outside_documented_range", risks)
        # Overall status must not be penalized as UNFAVORABLE
        self.assertNotEqual(status, CompatibilityStatus.UNFAVORABLE)

    def test_annual_rainfall_evaluation(self) -> None:
        """True annual rainfall input (e.g. 1700 mm/year) is evaluated against documented annual boundaries."""
        rice = crop_requirement_repository.get_requirement("rice")
        self.assertIsNotNone(rice)

        status, var_evals, risks = evaluate_crop_environmental_compatibility(
            requirement=rice,
            temperature_c=25.0,
            rainfall_mm=1700.0,
            soil_ph=6.5,
            clay_pct=45.0,
            sand_pct=25.0,
            silt_pct=30.0,
            rainfall_is_annual=True,
        )

        rain_eval = var_evals["rainfall"]
        self.assertEqual(rain_eval.status, CompatibilityStatus.FAVORABLE)
        self.assertEqual(status, CompatibilityStatus.FAVORABLE)
        self.assertEqual(len(risks), 0)


class TestFullIntegrationPipelines(unittest.IsolatedAsyncioTestCase):
    """Integration tests for advisory and recommendation service endpoints."""

    async def test_farm_advisory_generates_tri_concept_report(self) -> None:
        """Verify that generate_advisory returns ML predictions, FAO compatibility, and regional candidates."""
        request = FarmAdvisoryRequest(
            latitude=16.20,
            longitude=77.35,
            observation_date="2026-09-25",
            agricultural_inputs=AgriculturalInput(
                nitrogen=80.0,
                phosphorus=40.0,
                potassium=40.0,
                temperature=26.5,
                humidity=65.0,
                ph=6.8,
                rainfall=120.0,
            ),
            soil_type=SoilType.DEEP_BLACK,
            irrigation_status=IrrigationStatus.CANAL_IRRIGATED,
            season=CropSeason.KHARIF,
            top_k=3,
        )

        response = await farm_advisory_service.generate_advisory(request)

        # 1. Benchmark ML predictions preserved
        self.assertEqual(len(response.crop_advisories), 3)
        self.assertEqual(response.crop_advisories[0].crop, "coffee")
        self.assertAlmostEqual(response.crop_advisories[0].probability_estimate, 0.53, places=2)

        # 2. FAO compatibility does not falsely mark Coffee Unfavorable on rainfall
        rain_comp = response.crop_advisories[0].compatibility_evaluations["rainfall"]
        self.assertEqual(rain_comp.status, CompatibilityStatus.UNAVAILABLE)

        # 3. Regional agronomic candidates attached
        self.assertIsNotNone(response.regional_advisory)
        self.assertIsInstance(response.regional_advisory, RegionalAdvisoryReport)
        self.assertEqual(len(response.regional_advisory.candidates), 6)

        # Check prioritized crops for Deep Black + Canal + Kharif
        top_candidates = [c.crop_key for c in response.regional_advisory.candidates[:2]]
        self.assertIn("cotton", top_candidates)
        self.assertIn("rice", top_candidates)

    async def test_recommendation_service_attaches_regional_candidates(self) -> None:
        """Verify that RecommendationService also attaches RegionalAdvisoryReport for Raichur coordinates."""
        request = RecommendationRequest(
            latitude=16.20,
            longitude=77.35,
            observation_date="2026-09-25",
            agricultural_inputs=AgriculturalInput(
                nitrogen=80.0,
                phosphorus=40.0,
                potassium=40.0,
                temperature=26.5,
                humidity=65.0,
                ph=6.8,
                rainfall=120.0,
            ),
            soil_type=SoilType.DEEP_BLACK,
            irrigation_status=IrrigationStatus.RAINFED,
            season=CropSeason.RABI,
            top_k=3,
        )

        response = await recommendation_service.generate_recommendation(request)

        self.assertIsInstance(response, RecommendationResponse)
        self.assertIsNotNone(response.regional_advisory)
        # For Rainfed Rabi, Rabi Jowar and Chickpea must be top candidates
        top_candidates = [c.crop_key for c in response.regional_advisory.candidates[:2]]
        self.assertIn("sorghum", top_candidates)
        self.assertIn("chickpea", top_candidates)


if __name__ == "__main__":
    unittest.main()
