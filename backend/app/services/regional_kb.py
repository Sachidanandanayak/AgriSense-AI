"""Authoritative Regional Agronomic Knowledge Base for Raichur & Yadgir, Karnataka.

Grounded strictly in:
1. University of Agricultural Sciences (UAS), Raichur - Package of Practices (PoP)
   for High Yielding Crops (Dryland & Irrigated Agriculture).
   https://uasraichur.edu.in
2. ICAR - Krishi Vigyan Kendra (KVK) Raichur & KVK Yadgir (Kawadimatti)
   District Contingency Plans & Frontline Demonstrations.
   https://ataribengaluru.icar.gov.in
3. ICAR - National Bureau of Soil Survey and Land Use Planning (NBSS&LUP)
   Soils of Karnataka for Optimizing Land Use (Publ. 47) & Bhoomi Geoportal.
   https://bhoomi.karnataka.gov.in
4. Karnataka State Department of Agriculture (KSDA) District Profiles.
   https://raitamitra.karnataka.gov.in
5. FAO ECOCROP Ecological Database biophysical benchmarks.
   https://ecocrop.apps.fao.org
"""

from __future__ import annotations

import logging
from typing import Sequence

from app.schemas.regional import (
    CropSeason,
    IrrigationStatus,
    RegionalAdvisoryReport,
    RegionalCropCandidate,
    RegionalSuitabilityTier,
    SoilType,
)

logger = logging.getLogger(__name__)

# Regional coordinates bounding box for Raichur & Yadgir districts
RAICHUR_YADGIR_BOUNDS = {
    "lat_min": 15.6,
    "lat_max": 17.3,
    "lon_min": 76.2,
    "lon_max": 77.8,
}


def is_raichur_yadgir_region(latitude: float, longitude: float) -> bool:
    """Check whether coordinates fall within Raichur and Yadgir agro-climatic boundaries."""
    return (
        RAICHUR_YADGIR_BOUNDS["lat_min"] <= latitude <= RAICHUR_YADGIR_BOUNDS["lat_max"]
        and RAICHUR_YADGIR_BOUNDS["lon_min"] <= longitude <= RAICHUR_YADGIR_BOUNDS["lon_max"]
    )


# Authoritative Provenance URLs
UAS_RAICHUR_POP_URL = "https://uasraichur.edu.in/index.php/en/extension/package-of-practices"
KVK_YADGIR_URL = "https://ataribengaluru.icar.gov.in/kvk-yadgir.php"
ICAR_NBSSLUP_URL = "https://nbsslup.icar.gov.in"
KSDA_PORTAL_URL = "https://raitamitra.karnataka.gov.in"
FAO_ECOCROP_URL = "https://ecocrop.apps.fao.org"


def evaluate_regional_candidates(
    latitude: float,
    longitude: float,
    soil_type: SoilType | None = None,
    irrigation: IrrigationStatus | None = None,
    season: CropSeason | None = None,
    temperature_c: float | None = None,
    soil_ph: float | None = None,
) -> RegionalAdvisoryReport:
    """Evaluate locally relevant staple crops for Raichur & Yadgir without arbitrary scoring.

    Evaluates the 6 authoritative regional crops against confirmed farmer field conditions:
    1. Cotton (Gossypium hirsutum)
    2. Paddy / Rice (Oryza sativa)
    3. Pigeon Pea / Tur (Cajanus cajan)
    4. Rabi Jowar / Sorghum (Sorghum bicolor)
    5. Chickpea / Bengal Gram (Cicer arietinum)
    6. Groundnut (Arachis hypogaea)
    """
    candidates: list[RegionalCropCandidate] = []
    context_notes: list[str] = [
        "Regional evaluation based on UAS Raichur Package of Practices for Zone 2 (North Eastern Dry Zone).",
        "District aggregate soils comprise ~57.6% black soils (Vertisols) and ~42.4% red soils (Alfisols/chalka), but field-specific soil type governs individual parcel suitability.",
    ]

    if soil_type is None:
        context_notes.append("Field soil type was not confirmed by farmer; evaluating with generalized regional soil tolerance.")
    if irrigation is None:
        context_notes.append("Irrigation access was not confirmed by farmer; assuming conditional water availability.")
    if season is None:
        context_notes.append("Cropping season was not confirmed by farmer; evaluating seasonal requirements per crop.")

    # -------------------------------------------------------------------------
    # 1. COTTON (Gossypium hirsutum) - EcoCrop 913
    # -------------------------------------------------------------------------
    cotton_advice: list[str] = [
        "Major commercial cash crop of Raichur (historical 'Cotton City') and southern Yadgir.",
        "Deep black Vertisols retain monsoon rainfall, preventing flower shedding during dry spells.",
        "Recommended sowing spacing: 90 x 60 cm for Bt hybrids; adopt integrated pest management (IPM) for pink bollworm.",
    ]
    if season == CropSeason.RABI:
        cotton_tier = RegionalSuitabilityTier.TIER_3_INCOMPATIBLE
        cotton_label = "Incompatible (Season Mismatch)"
        cotton_soil_note = "Deep black Vertisol preferred, but Rabi sowing is unviable."
        cotton_water_note = "Unviable under winter sowing."
        cotton_advice.append("Cotton is a long-duration Kharif crop; late Rabi sowing causes heavy flower shedding and severe pest infestation.")
    elif season == CropSeason.KHARIF:
        if soil_type in (SoilType.DEEP_BLACK, SoilType.MEDIUM_BLACK) or soil_type is None:
            cotton_tier = RegionalSuitabilityTier.TIER_1_RECOMMENDED
            cotton_label = "Recommended Primary Candidate"
            cotton_soil_note = "Deep to medium black Vertisols (pH 7.2–8.5) provide high cation exchange capacity and moisture retention."
            cotton_water_note = "Rainfed Kharif or 2–3 supplemental irrigations via furrow/drip."
        else:  # Red sandy loam
            cotton_tier = RegionalSuitabilityTier.TIER_2_CONDITIONAL
            cotton_label = "Conditional (Requires Irrigation)"
            cotton_soil_note = "Red sandy loam (chalka) has lower moisture retention; cotton may suffer mid-season drought stress without frequent irrigation."
            cotton_water_note = "Requires assured supplementary irrigation on light soils."
    else:  # season is None or Summer
        cotton_tier = RegionalSuitabilityTier.TIER_2_CONDITIONAL
        cotton_label = "Conditional (Kharif Optimal)"
        cotton_soil_note = "Deep black Vertisol ideal; requires confirmation of Kharif sowing window."
        cotton_water_note = "Rainfed Kharif or irrigated."

    candidates.append(
        RegionalCropCandidate(
            crop_key="cotton",
            display_name="Cotton (Bt / Hybrid)",
            kannada_name="ಹತ್ತಿ (Hatti)",
            scientific_name="Gossypium hirsutum",
            ecocrop_code=913,
            suitability_tier=cotton_tier,
            tier_label=cotton_label,
            sowing_window="June 15 – July 15 (Kharif)",
            recommended_varieties=[
                "Bt Cotton Bollgard II approved hybrids",
                "RAH-100 (UAS Raichur)",
                "RAHS-14 (UAS Raichur)",
            ],
            soil_compatibility_note=cotton_soil_note,
            water_management_note=cotton_water_note,
            agronomic_advice=cotton_advice,
            provenance_sources=[
                f"UAS Raichur Package of Practices (Commercial Crops): {UAS_RAICHUR_POP_URL}",
                f"ICAR All India Coordinated Research Project on Cotton (Raichur Station): {ICAR_NBSSLUP_URL}",
            ],
        )
    )

    # -------------------------------------------------------------------------
    # 2. PADDY / RICE (Oryza sativa) - EcoCrop 1574
    # -------------------------------------------------------------------------
    rice_advice: list[str] = [
        "Cultivated extensively in Tungabhadra Left Bank Canal (TLBC) and Upper Krishna Project (UKP) command areas.",
        "Requires puddled clay soil or clay loam with well-compacted bunds to minimize percolation losses.",
        "Adopt alternate wetting and drying (AWD) or direct seeded rice (DSR) to conserve water (UAS Raichur PoP).",
    ]
    if irrigation == IrrigationStatus.RAINFED:
        rice_tier = RegionalSuitabilityTier.TIER_3_INCOMPATIBLE
        rice_label = "Incompatible (Severe Water Deficit)"
        rice_soil_note = "Heavy clay soil suitable for puddling, but lack of assured irrigation makes cultivation unviable."
        rice_water_note = "Rainfed annual precipitation (~700 mm) is strictly insufficient for flood/ponded paddy (~1200–1500 mm requirement)."
        rice_advice.append("UAS Raichur PoP explicitly discourages rainfed paddy in Zone 2 due to catastrophic drought failure risk.")
    elif irrigation in (IrrigationStatus.CANAL_IRRIGATED, IrrigationStatus.BOREWELL_IRRIGATED):
        if season in (CropSeason.KHARIF, CropSeason.SUMMER) or season is None:
            rice_tier = RegionalSuitabilityTier.TIER_1_RECOMMENDED
            rice_label = "Recommended Primary Candidate"
            rice_soil_note = "Deep black Vertisol or clay loam with high water holding capacity and impermeable subsoil layer."
            rice_water_note = "Canal or borewell water supply matches high crop evapotranspiration requirement."
        else:  # Rabi
            rice_tier = RegionalSuitabilityTier.TIER_2_CONDITIONAL
            rice_label = "Conditional (Cold Stress Risk)"
            rice_soil_note = "Puddled clay suitable."
            rice_water_note = "Assured irrigation available."
            rice_advice.append("Rabi winter paddy in Raichur suffers cold-induced spikelet sterility if flowering coincides with December-January night lows (<15°C).")
    else:  # irrigation is None
        rice_tier = RegionalSuitabilityTier.TIER_2_CONDITIONAL
        rice_label = "Conditional (Requires Assured Water)"
        rice_soil_note = "Deep black or clay loam required for water ponding."
        rice_water_note = "Requires confirmation of canal or borewell irrigation access before sowing."

    candidates.append(
        RegionalCropCandidate(
            crop_key="rice",
            display_name="Paddy (Rice)",
            kannada_name="ಭತ್ತ (Bhatta)",
            scientific_name="Oryza sativa",
            ecocrop_code=1574,
            suitability_tier=rice_tier,
            tier_label=rice_label,
            sowing_window="July – August (Kharif) or January – February (Summer)",
            recommended_varieties=[
                "BPT-5204 (Samba Mahsuri)",
                "RNR-15048 (Telangana Sona - Low GI)",
                "Gangavati Sona (GGV-0501 - UAS Raichur)",
            ],
            soil_compatibility_note=rice_soil_note,
            water_management_note=rice_water_note,
            agronomic_advice=rice_advice,
            provenance_sources=[
                f"UAS Raichur Package of Practices (Cereals): {UAS_RAICHUR_POP_URL}",
                f"Tungabhadra Command Area Development Authority (CADA): {KSDA_PORTAL_URL}",
            ],
        )
    )

    # -------------------------------------------------------------------------
    # 3. PIGEON PEA / TUR (Cajanus cajan) - EcoCrop 363
    # -------------------------------------------------------------------------
    tur_advice: list[str] = [
        "Yadgir district is recognized as the 'Daal Bowl of Karnataka', with specialized pulse market yards.",
        "Deep taproot system enables excellent drought endurance during dry spells.",
        "Highly sensitive to prolonged water stagnation and Phytophthora blight; adopt broad-bed furrow (BBF) or ridge sowing in heavy soils.",
    ]
    if season == CropSeason.RABI:
        tur_tier = RegionalSuitabilityTier.TIER_3_INCOMPATIBLE
        tur_label = "Incompatible (Season Mismatch)"
        tur_soil_note = "Well-drained soil suitable, but Rabi sowing causes vegetative stunting."
        tur_water_note = "Photoperiod sensitive; unviable in Rabi."
        tur_advice.append("Pigeon pea is photoperiod-sensitive and long-duration; post-monsoon sowing causes severe stunting and low pod set.")
    else:
        if soil_type == SoilType.DEEP_BLACK:
            tur_tier = RegionalSuitabilityTier.TIER_2_CONDITIONAL
            tur_label = "Conditional (Requires Drainage Management)"
            tur_soil_note = "Heavy clay Vertisol can waterlog during intense monsoon spells; ridge-and-furrow planting is mandatory to prevent root asphyxiation."
            tur_water_note = "Rainfed Kharif crop; highly drought-resilient once taproot penetrates subsoil."
        elif soil_type in (SoilType.MEDIUM_BLACK, SoilType.RED_SANDY_LOAM, SoilType.LOAM) or soil_type is None:
            tur_tier = RegionalSuitabilityTier.TIER_1_RECOMMENDED
            tur_label = "Recommended Primary Candidate"
            tur_soil_note = "Well-drained medium black or red sandy loam (pH 6.5–8.0) provides ideal root aeration and nodulation."
            tur_water_note = "Rainfed Kharif crop with low supplemental water needs."
        else:
            tur_tier = RegionalSuitabilityTier.TIER_2_CONDITIONAL
            tur_label = "Conditional"
            tur_soil_note = "Ensure adequate surface drainage."
            tur_water_note = "Rainfed."

    candidates.append(
        RegionalCropCandidate(
            crop_key="pigeonpeas",
            display_name="Pigeon Pea (Tur / Red Gram)",
            kannada_name="ತೊಗರಿ (Togari)",
            scientific_name="Cajanus cajan",
            ecocrop_code=363,
            suitability_tier=tur_tier,
            tier_label=tur_label,
            sowing_window="June 15 – July 15 (Kharif)",
            recommended_varieties=[
                "TS-3R (Wilt resistant - UAS Raichur / KVK Yadgir)",
                "GRG-811 (UAS Raichur)",
                "BSMR-736 (Sterility mosaic resistant)",
                "WRP-1 (UAS Raichur)",
            ],
            soil_compatibility_note=tur_soil_note,
            water_management_note=tur_water_note,
            agronomic_advice=tur_advice,
            provenance_sources=[
                f"KVK Yadgir (Kawadimatti) Daal Scheme: {KVK_YADGIR_URL}",
                f"UAS Raichur Package of Practices (Pulses): {UAS_RAICHUR_POP_URL}",
            ],
        )
    )

    # -------------------------------------------------------------------------
    # 4. RABI JOWAR / SORGHUM (Sorghum bicolor) - EcoCrop 1999
    # -------------------------------------------------------------------------
    jowar_advice: list[str] = [
        "Flagship food and fodder grain of North Karnataka dryland agro-ecosystem.",
        "Cultivated predominantly on residual soil moisture conserved in deep Vertisols during the receding monsoon.",
        "Sowing must be completed between September 15 and October 15; delayed sowing leads to severe shoot fly (Atherigona soccata) infestation.",
    ]
    if season in (CropSeason.KHARIF, CropSeason.SUMMER):
        jowar_tier = RegionalSuitabilityTier.TIER_3_INCOMPATIBLE
        jowar_label = "Incompatible (Season Mismatch)"
        jowar_soil_note = "Vertisols ideal, but season incompatible."
        jowar_water_note = "Unviable under monsoon rain or summer heat."
        jowar_advice.append("Maldandi cultivars sown in Kharif suffer severe grain mold from monsoon rains; summer heat causes pollen sterility.")
    elif season == CropSeason.RABI or season is None:
        if soil_type in (SoilType.DEEP_BLACK, SoilType.MEDIUM_BLACK) or soil_type is None:
            jowar_tier = RegionalSuitabilityTier.TIER_1_RECOMMENDED
            jowar_label = "Recommended Primary Candidate"
            jowar_soil_note = "Deep black Vertisol (high smectite clay) stores 180–220 mm/m of available moisture, sustaining post-monsoon crop growth."
            jowar_water_note = "Entirely rainfed on conserved residual soil moisture; 1 protective irrigation at boot leaf stage significantly boosts grain weight."
        else:  # Red sandy loam
            jowar_tier = RegionalSuitabilityTier.TIER_3_INCOMPATIBLE
            jowar_label = "Incompatible (Insufficient Soil Moisture Retention)"
            jowar_soil_note = "Red sandy loam (chalka) lacks moisture holding capacity to sustain rainfed post-monsoon Sorghum."
            jowar_water_note = "Rainfed Rabi Sorghum requires deep black soil with high moisture retention."
            jowar_advice.append("UAS Raichur PoP restricts rainfed Rabi Sorghum to deep/medium black soils; red soils dry out before panicle emergence.")
    else:
        jowar_tier = RegionalSuitabilityTier.TIER_2_CONDITIONAL
        jowar_label = "Conditional"
        jowar_soil_note = "Requires deep black moisture-retaining soil."
        jowar_water_note = "Residual moisture dependent."

    candidates.append(
        RegionalCropCandidate(
            crop_key="sorghum",
            display_name="Rabi Jowar (Sorghum)",
            kannada_name="ಜೋಳ (Jola)",
            scientific_name="Sorghum bicolor",
            ecocrop_code=1999,
            suitability_tier=jowar_tier,
            tier_label=jowar_label,
            sowing_window="September 15 – October 15 (Rabi)",
            recommended_varieties=[
                "Maldandi (M 35-1 - Heritage sweet grain & tall fodder)",
                "CSV-22R (High yielding rabi jowar)",
                "CSV-29R",
                "BJV-44 (UAS Raichur)",
            ],
            soil_compatibility_note=jowar_soil_note,
            water_management_note=jowar_water_note,
            agronomic_advice=jowar_advice,
            provenance_sources=[
                f"UAS Raichur Package of Practices (Millets): {UAS_RAICHUR_POP_URL}",
                f"AICRP on Sorghum (Raichur & Hagari Stations): {ICAR_NBSSLUP_URL}",
            ],
        )
    )

    # -------------------------------------------------------------------------
    # 5. CHICKPEA / BENGAL GRAM (Cicer arietinum) - EcoCrop 751
    # -------------------------------------------------------------------------
    chickpea_advice: list[str] = [
        "Major post-monsoon pulse grown across black soils of Raichur, Yadgir, and Kalaburagi.",
        "Requires cool, dry climate during vegetative phase and warm conditions during pod filling.",
        "Seed treatment with Trichoderma viride and Rhizobium is strongly recommended to protect against Fusarium wilt.",
    ]
    if season in (CropSeason.KHARIF, CropSeason.SUMMER):
        chickpea_tier = RegionalSuitabilityTier.TIER_3_INCOMPATIBLE
        chickpea_label = "Incompatible (Season Mismatch)"
        chickpea_soil_note = "Black soil suitable, but monsoon/summer climate incompatible."
        chickpea_water_note = "Excessive moisture or heat causes collar rot and root rot."
        chickpea_advice.append("Chickpea is strictly a cool-season Rabi crop; monsoon sowing causes damping off and complete mortality.")
    elif season == CropSeason.RABI or season is None:
        if soil_type in (SoilType.DEEP_BLACK, SoilType.MEDIUM_BLACK, SoilType.LOAM) or soil_type is None:
            chickpea_tier = RegionalSuitabilityTier.TIER_1_RECOMMENDED
            chickpea_label = "Recommended Primary Candidate"
            chickpea_soil_note = "Deep to medium black Vertisol (pH 6.8–8.5) with moderate internal drainage and neutral to alkaline reaction."
            chickpea_water_note = "Grown on residual moisture; 1 protective irrigation at pod initiation (45–50 DAS) yields substantial return."
        else:  # Red sandy loam
            chickpea_tier = RegionalSuitabilityTier.TIER_2_CONDITIONAL
            chickpea_label = "Conditional (Requires Supplementary Irrigation)"
            chickpea_soil_note = "Red sandy loam dries quickly in post-monsoon winter; requires 1–2 supplemental irrigations."
            chickpea_water_note = "Supplementary irrigation needed on lighter soils."
    else:
        chickpea_tier = RegionalSuitabilityTier.TIER_2_CONDITIONAL
        chickpea_label = "Conditional"
        chickpea_soil_note = "Black soil preferred."
        chickpea_water_note = "Residual moisture."

    candidates.append(
        RegionalCropCandidate(
            crop_key="chickpea",
            display_name="Chickpea (Bengal Gram / Chana)",
            kannada_name="ಕಡಲೆ (Kadale)",
            scientific_name="Cicer arietinum",
            ecocrop_code=751,
            suitability_tier=chickpea_tier,
            tier_label=chickpea_label,
            sowing_window="October 15 – November 15 (Rabi)",
            recommended_varieties=[
                "JG-11 (Widely adopted wilt-tolerant variety)",
                "Super Annigeri-1 (BGD-111-1 - UAS Raichur)",
                "JAK-9218",
            ],
            soil_compatibility_note=chickpea_soil_note,
            water_management_note=chickpea_water_note,
            agronomic_advice=chickpea_advice,
            provenance_sources=[
                f"UAS Raichur Package of Practices (Pulses): {UAS_RAICHUR_POP_URL}",
                f"AICRP on Chickpea (ICAR - UAS Raichur): {KVK_YADGIR_URL}",
            ],
        )
    )

    # -------------------------------------------------------------------------
    # 6. GROUNDNUT / PEANUT (Arachis hypogaea) - EcoCrop 347
    # -------------------------------------------------------------------------
    groundnut_advice: list[str] = [
        "Light texture friable soil is critical for subterranean pod pegging and clean harvesting.",
        "Apply Gypsum at 500 kg/ha at peg initiation (30–40 DAS) to ensure calcium availability for shell hardening and prevent 'pops' (empty pods).",
    ]
    if soil_type == SoilType.DEEP_BLACK:
        groundnut_tier = RegionalSuitabilityTier.TIER_2_CONDITIONAL
        groundnut_label = "Conditional (Soil Texture Limitation)"
        groundnut_soil_note = "Heavy cracking black clay (Vertisol, clay >40%) swells when wet and hardens into clods when dry, severely restricting gynophore (peg) penetration and causing pod detachment during digging. Red sandy loam/chalka preferred (UAS Raichur PoP)."
        groundnut_water_note = "Heavy clay soil retains water but creates poor physical conditions for pegging."
        groundnut_advice.append("UAS Raichur PoP cautions against groundnut in deep cracking black soils due to high harvesting loss; red sandy loam is recommended.")
    elif soil_type in (SoilType.RED_SANDY_LOAM, SoilType.LOAM) or soil_type is None:
        if season == CropSeason.KHARIF:
            groundnut_tier = RegionalSuitabilityTier.TIER_1_RECOMMENDED
            groundnut_label = "Recommended Primary Candidate"
            groundnut_soil_note = "Red sandy loam (chalka / Alfisol, pH 6.0–7.5) provides loose, friable seedbed allowing easy peg penetration."
            groundnut_water_note = "Rainfed Kharif crop; benefits from well-distributed monsoon showers."
        elif season == CropSeason.SUMMER:
            if irrigation in (IrrigationStatus.CANAL_IRRIGATED, IrrigationStatus.BOREWELL_IRRIGATED):
                groundnut_tier = RegionalSuitabilityTier.TIER_1_RECOMMENDED
                groundnut_label = "Recommended Primary Candidate (Irrigated Summer)"
                groundnut_soil_note = "Friable red sandy loam or light loam."
                groundnut_water_note = "Requires assured sprinkler or furrow irrigation every 7–10 days in summer."
            else:
                groundnut_tier = RegionalSuitabilityTier.TIER_3_INCOMPATIBLE
                groundnut_label = "Incompatible (Summer Water Deficit)"
                groundnut_soil_note = "Red sandy loam suitable."
                groundnut_water_note = "Summer groundnut cannot survive without assured irrigation."
                groundnut_advice.append("Summer groundnut in Raichur (March-May temperatures >40°C) requires assured irrigation every 7-10 days.")
        else:  # Rabi or None
            groundnut_tier = RegionalSuitabilityTier.TIER_2_CONDITIONAL
            groundnut_label = "Conditional"
            groundnut_soil_note = "Friable red sandy loam preferred."
            groundnut_water_note = "Rainfed Kharif or irrigated summer."
    else:
        groundnut_tier = RegionalSuitabilityTier.TIER_2_CONDITIONAL
        groundnut_label = "Conditional"
        groundnut_soil_note = "Ensure friable topsoil for pegging."
        groundnut_water_note = "Manage moisture according to season."

    candidates.append(
        RegionalCropCandidate(
            crop_key="groundnut",
            display_name="Groundnut (Peanut)",
            kannada_name="ಕಡಲೆಕಾಯಿ (Kadalekayi)",
            scientific_name="Arachis hypogaea",
            ecocrop_code=347,
            suitability_tier=groundnut_tier,
            tier_label=groundnut_label,
            sowing_window="June – July (Kharif) or January – February (Summer)",
            recommended_varieties=[
                "TMV-2 (Traditional bunch type)",
                "GPBD-4 (Rust & late leaf spot resistant - UAS Dharwad / Raichur)",
                "K-9 (High yielding)",
                "Kadiri-6",
            ],
            soil_compatibility_note=groundnut_soil_note,
            water_management_note=groundnut_water_note,
            agronomic_advice=groundnut_advice,
            provenance_sources=[
                f"UAS Raichur Package of Practices (Oilseeds): {UAS_RAICHUR_POP_URL}",
                f"AICRP on Groundnut (Raichur Station): {KSDA_PORTAL_URL}",
            ],
        )
    )

    # Sort candidates by tier order (Tier 1 -> Tier 2 -> Tier 3)
    tier_order = {
        RegionalSuitabilityTier.TIER_1_RECOMMENDED: 1,
        RegionalSuitabilityTier.TIER_2_CONDITIONAL: 2,
        RegionalSuitabilityTier.TIER_3_INCOMPATIBLE: 3,
    }
    candidates.sort(key=lambda c: tier_order.get(c.suitability_tier, 99))

    return RegionalAdvisoryReport(
        region_name="Karnataka Zone 2 (North Eastern Dry Zone) & Zone 1 (NE Transition)",
        districts=["Raichur", "Yadgir"],
        field_soil_type=soil_type,
        irrigation_access=irrigation,
        cropping_season=season,
        candidates=candidates,
        context_notes=context_notes,
    )
