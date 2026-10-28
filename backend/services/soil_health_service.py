"""
IRRIGATEWISE — Soil Health Monitoring & Potting Mix Interpretation Service
Calibrated specifically for 15L Terrace Garden Container Cultivation
(Cocopeat + Vermicompost + Perlite 50:30:20 with Hydrogel SAP buffer)
"""

from typing import List, Dict, Optional, Any
from schemas import (
    NutrientReadingDetail,
    SoilHealthMonitoringOutput
)

# Reference ranges for balanced organic terrace potting mix (mg/kg or ppm dry basis)
POTTING_MIX_CALIBRATION = {
    "nitrogen": {
        "min": 80.0,
        "max": 140.0,
        "unit": "mg/kg",
        "low_remedy": "Top-dress with 100g vermicompost or apply diluted fish amino acid (5ml/L) / mustard oil cake tea.",
        "high_remedy": "Excess nitrogen promotes lush foliage at the expense of fruiting. Flush container gently with water and suspend compost tea.",
        "deficiency_symptom": "Chlorosis (yellowing) starting from older lower leaves, stunted vegetative growth.",
        "excess_symptom": "Dark green, overly soft foliage with poor flower set and susceptibility to aphids."
    },
    "phosphorus": {
        "min": 30.0,
        "max": 60.0,
        "unit": "mg/kg",
        "low_remedy": "Incorporate 1 tablespoon steamed bone meal or rock phosphate powder into the top 2 inches of potting mix.",
        "high_remedy": "High phosphorus can bind zinc and iron. Water with plain rainwater or aged tap water; withhold phosphorus fertilizers.",
        "deficiency_symptom": "Purplish or bronze discoloration along lower leaf veins, delayed root establishment.",
        "excess_symptom": "Micro-nutrient lockout, especially iron and zinc chlorosis in younger leaves."
    },
    "potassium": {
        "min": 150.0,
        "max": 250.0,
        "unit": "mg/kg",
        "low_remedy": "Feed with fermented banana peel extract (diluted 1:5) or wood ash (1 teaspoon per 15L pot; avoid if pH > 7.0).",
        "high_remedy": "Excess potassium can hinder calcium and magnesium uptake. Flush container with water.",
        "deficiency_symptom": "Marginal leaf scorch (burnt leaf edges) and poor blossom development.",
        "excess_symptom": "Interveinal chlorosis in younger leaves caused by magnesium competition."
    },
    "ph": {
        "min": 5.8,
        "max": 6.8,
        "unit": "pH",
        "low_remedy": "Add 1 tablespoon agricultural lime (calcium carbonate) or dolomite per 15L container to raise pH.",
        "high_remedy": "Blend crushed bio-char, sulfur powder (half teaspoon), or well-cured leaf mold to bring pH down.",
        "deficiency_symptom": "Acidic medium (<5.5) locks out phosphorus, calcium, and magnesium.",
        "excess_symptom": "Alkaline medium (>7.2) causes severe iron chlorosis in acid-loving container plants."
    },
    "moisture": {
        "min": 50.0,
        "max": 70.0,
        "unit": "%",
        "low_remedy": "Irrigate with 350-500 mL water per pot. Allow hydrogel beads to rehydrate and swell.",
        "high_remedy": "Halt watering. Check drainage holes for cocopeat compaction; improve aeration.",
        "deficiency_symptom": "Temporary wilting, hydrogel bead shrinkage, premature blossom drop.",
        "excess_symptom": "Root hypoxia, fungus gnat infestation, damping off in young container seedlings."
    }
}

PLANT_NUTRIENT_DEMANDS = {
    "Tomato": {
        "stage_needs": {
            "Vegetative": "Balanced N (100 mg/kg) and K (160 mg/kg) for stem development.",
            "Flowering": "Lower N, increase P (50 mg/kg) and K (220 mg/kg) for strong blossom cluster retention.",
            "Fruiting": "Heavy K demand (220-250 mg/kg) with adequate calcium to prevent Blossom End Rot."
        },
        "opt_ph": "6.0 - 6.8"
    },
    "Chili": {
        "stage_needs": {
            "Vegetative": "Moderate N (90-110 mg/kg). Avoid over-fertilizing to prevent delayed flowering.",
            "Flowering": "High K (180-220 mg/kg) and micronutrients (Zinc, Boron) to minimize flower drop.",
            "Fruiting": "Steady potassium and moderate phosphorus with controlled moisture."
        },
        "opt_ph": "6.0 - 6.8"
    },
    "Spinach (Palak)": {
        "stage_needs": {
            "Vegetative": "High N (120-140 mg/kg) for rapid leafy harvest. Maintain steady moisture with hydrogel.",
            "Mature": "Harvest outer leaves; replenish with light liquid vermicompost wash weekly."
        },
        "opt_ph": "6.2 - 7.0"
    },
    "Mint (Pudina)": {
        "stage_needs": {
            "Vegetative": "Generous organic nitrogen and constant high moisture (60-70%). Excellent hydrogel responder."
        },
        "opt_ph": "6.0 - 7.0"
    },
    "Tulsi (Holy Basil)": {
        "stage_needs": {
            "Vegetative": "Lean to moderate nutrient profile (N: 80-100 mg/kg). High nitrogen dilutes essential aromatic oils.",
            "Flowering": "Pinch off flower spires (Manjari) to maintain vegetative vigor and essential oil density."
        },
        "opt_ph": "6.2 - 7.2"
    },
    "Brinjal (Eggplant)": {
        "stage_needs": {
            "Vegetative": "High nitrogen and organic carbon for vigorous branching.",
            "Flowering": "High potassium and phosphorus with steady hydrogel moisture buffering."
        },
        "opt_ph": "5.8 - 6.8"
    }
}


class SoilHealthService:
    @classmethod
    def evaluate_potting_mix(
        cls,
        nitrogen: float,
        phosphorus: float,
        potassium: float,
        ph: float,
        organic_carbon: Optional[float] = 0.85,
        moisture: Optional[float] = 58.0,
        plant_type: Optional[str] = None,
        growth_stage: Optional[str] = "Vegetative",
        hydrogel_present: bool = True
    ) -> SoilHealthMonitoringOutput:
        """
        Evaluates soil test values against terrace container cocopeat mix standards.
        """
        readings: List[NutrientReadingDetail] = []
        scores: List[float] = []

        # 1. Evaluate Nitrogen
        n_ref = POTTING_MIX_CALIBRATION["nitrogen"]
        if nitrogen < n_ref["min"]:
            n_status = "Deficient"
            n_score = max(20.0, (nitrogen / n_ref["min"]) * 60)
            n_interp = f"Nitrogen is below container benchmark ({nitrogen:.1f} vs {n_ref['min']}-{n_ref['max']} mg/kg). {n_ref['deficiency_symptom']}"
            n_remedy = n_ref["low_remedy"]
        elif nitrogen > n_ref["max"]:
            n_status = "Excessive"
            n_score = 65.0
            n_interp = f"Nitrogen is elevated ({nitrogen:.1f} mg/kg). {n_ref['excess_symptom']}"
            n_remedy = n_ref["high_remedy"]
        else:
            n_status = "Optimal"
            n_score = 95.0
            n_interp = f"Nitrogen is well balanced for container vegetative health ({nitrogen:.1f} mg/kg)."
            n_remedy = "Maintain current vermicompost feeding schedule (monthly 50g top-dress)."

        readings.append(NutrientReadingDetail(
            parameter="Nitrogen (Available N)",
            reading_value=round(nitrogen, 1),
            unit="mg/kg",
            status=n_status,
            calibrated_range="80.0 – 140.0 mg/kg",
            sensor_tolerance="±12% sensor variance",
            interpretation=n_interp,
            organic_remediation=n_remedy
        ))
        scores.append(n_score)

        # 2. Evaluate Phosphorus
        p_ref = POTTING_MIX_CALIBRATION["phosphorus"]
        if phosphorus < p_ref["min"]:
            p_status = "Deficient"
            p_score = max(20.0, (phosphorus / p_ref["min"]) * 60)
            p_interp = f"Phosphorus is low ({phosphorus:.1f} vs {p_ref['min']}-{p_ref['max']} mg/kg). {p_ref['deficiency_symptom']}"
            p_remedy = p_ref["low_remedy"]
        elif phosphorus > p_ref["max"]:
            p_status = "Excessive"
            p_score = 70.0
            p_interp = f"Phosphorus is elevated ({phosphorus:.1f} mg/kg). {p_ref['excess_symptom']}"
            p_remedy = p_ref["high_remedy"]
        else:
            p_status = "Optimal"
            p_score = 95.0
            p_interp = f"Phosphorus is at optimal concentration for container root growth and bud initiation."
            p_remedy = "Adequate for ongoing root metabolism. No intervention needed."

        readings.append(NutrientReadingDetail(
            parameter="Phosphorus (Olsen P)",
            reading_value=round(phosphorus, 1),
            unit="mg/kg",
            status=p_status,
            calibrated_range="30.0 – 60.0 mg/kg",
            sensor_tolerance="±10% sensor variance",
            interpretation=p_interp,
            organic_remediation=p_remedy
        ))
        scores.append(p_score)

        # 3. Evaluate Potassium
        k_ref = POTTING_MIX_CALIBRATION["potassium"]
        if potassium < k_ref["min"]:
            k_status = "Deficient"
            k_score = max(20.0, (potassium / k_ref["min"]) * 60)
            k_interp = f"Potassium is deficient ({potassium:.1f} vs {k_ref['min']}-{k_ref['max']} mg/kg). {k_ref['deficiency_symptom']}"
            k_remedy = k_ref["low_remedy"]
        elif potassium > k_ref["max"]:
            k_status = "Excessive"
            k_score = 75.0
            k_interp = f"Potassium is elevated ({potassium:.1f} mg/kg). {k_ref['excess_symptom']}"
            k_remedy = k_ref["high_remedy"]
        else:
            k_status = "Optimal"
            k_score = 95.0
            k_interp = f"Potassium is optimal ({potassium:.1f} mg/kg) supporting osmotic regulation and fruit firmness."
            k_remedy = "Healthy potassium buffer. Hydrogel matrix helps retain dissolved K+ cations against drainage runoff."

        readings.append(NutrientReadingDetail(
            parameter="Potassium (Exchangeable K)",
            reading_value=round(potassium, 1),
            unit="mg/kg",
            status=k_status,
            calibrated_range="150.0 – 250.0 mg/kg",
            sensor_tolerance="±10% sensor variance",
            interpretation=k_interp,
            organic_remediation=k_remedy
        ))
        scores.append(k_score)

        # 4. Evaluate pH
        ph_ref = POTTING_MIX_CALIBRATION["ph"]
        if ph < ph_ref["min"]:
            ph_status = "Acidic (Deficient)"
            ph_score = max(30.0, 100 - (ph_ref["min"] - ph) * 40)
            ph_interp = f"Potting mix is too acidic ({ph:.2f}). {ph_ref['deficiency_symptom']}"
            ph_remedy = ph_ref["low_remedy"]
        elif ph > ph_ref["max"]:
            ph_status = "Alkaline (Excessive)"
            ph_score = max(30.0, 100 - (ph - ph_ref["max"]) * 35)
            ph_interp = f"Potting mix is mildly alkaline ({ph:.2f}). {ph_ref['excess_symptom']}"
            ph_remedy = ph_ref["high_remedy"]
        else:
            ph_status = "Optimal"
            ph_score = 98.0
            ph_interp = f"Potting medium pH ({ph:.2f}) is in the prime nutrient assimilation window (5.8–6.8)."
            ph_remedy = "Maintain current moisture level; cocopeat maintains a naturally stable sub-acidic buffer."

        readings.append(NutrientReadingDetail(
            parameter="pH Acidity / Alkalinity",
            reading_value=round(ph, 2),
            unit="pH",
            status=ph_status,
            calibrated_range="5.8 – 6.8",
            sensor_tolerance="±0.15 pH unit",
            interpretation=ph_interp,
            organic_remediation=ph_remedy
        ))
        scores.append(ph_score)

        # Overall fertility calculation
        fertility_index = round(sum(scores) / len(scores), 1)
        if fertility_index >= 85:
            grade = "Prime Balanced"
        elif fertility_index >= 70:
            grade = "Good Fertility"
        elif fertility_index >= 50:
            grade = "Moderate (Correction Recommended)"
        else:
            grade = "Depleted (Immediate Nutrition Required)"

        # Hydrogel Retention Effect Description
        if hydrogel_present:
            hydrogel_effect = (
                "Potassium Polyacrylate Hydrogel SAP (25g/15L pot) is actively functioning as a reversible nutrient reservoir. "
                "Cation exchange research confirms SAP traps dissolved ammonium (NH4+) and potassium (K+) ions within its "
                "crosslinked 3D polymeric mesh, reducing drain-hole leaching losses by 36% to 42% compared to raw cocopeat."
            )
        else:
            hydrogel_effect = (
                "Hydrogel amendment absent. In 15L container grow bags with lightweight cocopeat, standard overhead watering "
                "typically washes away 40–55% of water-soluble nitrogen and potassium through bottom aeration perforations."
            )

        # Plant-specific guidance
        plant_advisories = []
        target_plant = plant_type if plant_type and plant_type in PLANT_NUTRIENT_DEMANDS else "Tomato"
        spec = PLANT_NUTRIENT_DEMANDS.get(target_plant, PLANT_NUTRIENT_DEMANDS["Tomato"])
        plant_advisories.append({
            "plant": target_plant,
            "optimal_ph": spec["opt_ph"],
            "growth_stage": growth_stage,
            "stage_specific_demand": spec["stage_needs"].get(growth_stage, list(spec["stage_needs"].values())[0])
        })

        # Add general companion notes
        if target_plant != "Tulsi (Holy Basil)":
            tulsi_spec = PLANT_NUTRIENT_DEMANDS["Tulsi (Holy Basil)"]
            plant_advisories.append({
                "plant": "Tulsi (Holy Basil)",
                "optimal_ph": tulsi_spec["opt_ph"],
                "growth_stage": "Vegetative",
                "stage_specific_demand": tulsi_spec["stage_needs"]["Vegetative"]
            })

        sensor_accuracy = (
            "NOTICE ON MEASUREMENT TOLERANCES: Low-cost optical and 3-in-1 multi-prong soil probes have an operational "
            "margin of ±10–15% compared to professional wet-chemistry lab assays (e.g., Alkaline Permanganate for N, "
            "Bray/Olsen for P, Ammonium Acetate flame photometry for K). Use these sensor readings to monitor trends "
            "over days rather than micro-adjusting organic fertilizers on hourly fluctuations."
        )

        return SoilHealthMonitoringOutput(
            container_potting_mix="Cocopeat : Vermicompost : Perlite (50:30:20) in 15L Container",
            overall_fertility_index=fertility_index,
            fertility_grade=grade,
            readings=readings,
            hydrogel_retention_effect=hydrogel_effect,
            plant_specific_advisories=plant_advisories,
            sensor_accuracy_notice=sensor_accuracy
        )
