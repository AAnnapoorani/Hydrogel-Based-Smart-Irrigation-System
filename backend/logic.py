from schemas import SoilInput, SoilAnalysisResult, IrrigationInput, IrrigationResult
from typing import List


SOIL_COEFFICIENTS = {
    "clay": 1.1,
    "loam": 0.85,
    "sandy": 0.65,
    "silt": 1.0,
}

CROP_DATABASE = [
    {"name": "Samba Rice",    "emoji": "🌾", "min_n": 70, "min_p": 30, "min_k": 150, "ph_min": 5.5, "ph_max": 7.5, "min_oc": 0.5,  "base_score": 90},
    {"name": "Sugarcane",     "emoji": "🍬", "min_n": 80, "min_p": 25, "min_k": 180, "ph_min": 6.0, "ph_max": 7.5, "min_oc": 0.6,  "base_score": 88},
    {"name": "Black Gram",    "emoji": "🫘", "min_n": 50, "min_p": 20, "min_k": 100, "ph_min": 5.5, "ph_max": 7.5, "min_oc": 0.4,  "base_score": 80},
    {"name": "Groundnut",     "emoji": "🥜", "min_n": 40, "min_p": 25, "min_k": 120, "ph_min": 6.0, "ph_max": 7.0, "min_oc": 0.5,  "base_score": 78},
    {"name": "Cotton",        "emoji": "🌿", "min_n": 60, "min_p": 30, "min_k": 140, "ph_min": 6.0, "ph_max": 8.0, "min_oc": 0.4,  "base_score": 72},
    {"name": "Maize",         "emoji": "🌽", "min_n": 65, "min_p": 25, "min_k": 120, "ph_min": 5.8, "ph_max": 7.0, "min_oc": 0.45, "base_score": 75},
    {"name": "Green Gram",    "emoji": "🌱", "min_n": 45, "min_p": 20, "min_k": 90,  "ph_min": 5.5, "ph_max": 7.5, "min_oc": 0.35, "base_score": 74},
    {"name": "Finger Millet", "emoji": "🌾", "min_n": 40, "min_p": 15, "min_k": 80,  "ph_min": 5.0, "ph_max": 8.0, "min_oc": 0.3,  "base_score": 70},
]

TRADITIONAL_IRRIGATION = 22.0  # L/m² baseline


class SoilAnalyzer:
    @staticmethod
    def analyze(soil: SoilInput) -> SoilAnalysisResult:
        # Nutrient scoring (0–100 per nutrient)
        n_score = min(100.0, (soil.nitrogen / 120) * 100)
        p_score = min(100.0, (soil.phosphorus / 60) * 100)
        k_score = min(100.0, (soil.potassium / 250) * 100)

        if 6.0 <= soil.ph <= 7.5:
            ph_score = 100.0
        elif 5.5 <= soil.ph <= 8.0:
            ph_score = 60.0
        else:
            ph_score = 25.0

        oc_score = min(100.0, (soil.organic_carbon / 0.75) * 100)

        # Weighted fertility score
        fertility = round(
            n_score * 0.30 + p_score * 0.20 + k_score * 0.20 +
            ph_score * 0.15 + oc_score * 0.15, 1
        )
        fertility = max(5.0, min(98.0, fertility))

        classification = "High" if fertility >= 70 else "Medium" if fertility >= 45 else "Low"

        # Crop matching
        matched_crops = []
        for crop in CROP_DATABASE:
            if (soil.nitrogen >= crop["min_n"] and soil.phosphorus >= crop["min_p"] and
                    soil.potassium >= crop["min_k"] and crop["ph_min"] <= soil.ph <= crop["ph_max"] and
                    soil.organic_carbon >= crop["min_oc"]):
                bonus = min(10, (soil.nitrogen - crop["min_n"]) / 10)
                score = round(min(99, crop["base_score"] + bonus))
                matched_crops.append({"name": f'{crop["emoji"]} {crop["name"]}', "match_score": score})

        if not matched_crops:
            matched_crops = [{"name": "🌾 Finger Millet", "match_score": 60}]

        matched_crops.sort(key=lambda x: x["match_score"], reverse=True)

        # Recommendations
        recs = []
        if soil.nitrogen < 80:
            recs.append(f"Apply urea (46-0-0) at 120–150 kg/ha. Current N: {soil.nitrogen} mg/kg (target: 80–120)")
        if soil.phosphorus < 30:
            recs.append(f"Add single superphosphate at 100 kg/ha. Current P: {soil.phosphorus} mg/kg (target: 30–60)")
        if soil.potassium < 120:
            recs.append(f"Apply muriate of potash (MOP) at 80 kg/ha. Current K: {soil.potassium} mg/kg (target: 120–250)")
        if soil.ph < 6.0:
            recs.append(f"Apply agricultural lime at 2–4 t/ha to raise pH from {soil.ph} to 6.0–7.5")
        if soil.ph > 7.5:
            recs.append(f"Apply sulfur at 200–400 kg/ha to lower pH from {soil.ph} to 6.0–7.5")
        if soil.organic_carbon < 0.75:
            recs.append(f"Incorporate FYM/compost at 5–10 t/ha. Current OC: {soil.organic_carbon}% (target: >0.75%)")
        if not recs:
            recs.append("Excellent soil health! Continue current management. Schedule re-testing in 3 months.")

        return SoilAnalysisResult(
            fertility_score=fertility,
            classification=classification,
            nutrient_scores={
                "nitrogen": round(n_score, 1),
                "phosphorus": round(p_score, 1),
                "potassium": round(k_score, 1),
                "ph": ph_score,
                "organic_carbon": round(oc_score, 1),
            },
            recommended_crops=matched_crops[:5],
            recommendations=recs,
        )


class IrrigationCalculator:
    @staticmethod
    def calculate(data: IrrigationInput) -> IrrigationResult:
        alpha = SOIL_COEFFICIENTS.get("loam", 0.85)
        # Allow override from input if alpha passed
        if hasattr(data, "alpha") and data.alpha:
            alpha = data.alpha

        smd = max(0.0, data.sm_optimal - data.sm_current)
        ir = round(alpha * smd, 2)
        total = round(ir * data.field_area, 0)
        saved = round((1 - ir / TRADITIONAL_IRRIGATION) * 100, 1) if ir < TRADITIONAL_IRRIGATION else 0.0
        saved = max(0.0, saved)

        if saved >= 30:
            efficiency = "Excellent"
        elif saved >= 20:
            efficiency = "Good"
        elif saved >= 10:
            efficiency = "Moderate"
        else:
            efficiency = "Low"

        return IrrigationResult(
            smd=round(smd, 2),
            irrigation_required=ir,
            total_water_litres=total,
            water_saved=saved,
            efficiency_rating=efficiency,
        )
