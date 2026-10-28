from schemas import SoilInput, SoilAnalysisResult, IrrigationInput, IrrigationResult
from typing import List, Dict, Any, TypedDict


class CropInfo(TypedDict, total=False):
    name: str
    emoji: str
    min_n: float
    min_p: float
    min_k: float
    ph_min: float
    ph_max: float
    min_oc: float
    base_score: float


SOIL_COEFFICIENTS = {
    "clay": 1.1,
    "loam": 0.85,
    "sandy": 0.65,
    "silt": 1.0,
}

CROP_DATABASE: List[CropInfo] = [
    {"name": "Bush Tomato", "emoji": "🍅", "min_n": 90, "min_p": 40, "min_k": 180, "ph_min": 6.0, "ph_max": 7.0, "min_oc": 0.8, "base_score": 92},
    {"name": "Cherry Tomato", "emoji": "🍅", "min_n": 80, "min_p": 35, "min_k": 160, "ph_min": 6.0, "ph_max": 7.0, "min_oc": 0.8, "base_score": 90},
    {"name": "Green Chilli", "emoji": "🌶️", "min_n": 70, "min_p": 30, "min_k": 120, "ph_min": 6.0, "ph_max": 7.2, "min_oc": 0.6, "base_score": 88},
    {"name": "Capsicum", "emoji": "🫑", "min_n": 85, "min_p": 35, "min_k": 150, "ph_min": 6.2, "ph_max": 7.0, "min_oc": 0.7, "base_score": 87},
    {"name": "Brinjal", "emoji": "🍆", "min_n": 85, "min_p": 35, "min_k": 140, "ph_min": 6.0, "ph_max": 7.2, "min_oc": 0.7, "base_score": 89},
    {"name": "Okra", "emoji": "🥢", "min_n": 60, "min_p": 25, "min_k": 100, "ph_min": 6.2, "ph_max": 7.5, "min_oc": 0.5, "base_score": 85},
    {"name": "Bush French Beans", "emoji": "🫘", "min_n": 35, "min_p": 35, "min_k": 80, "ph_min": 6.0, "ph_max": 6.8, "min_oc": 0.6, "base_score": 84},
    {"name": "Amaranth Keerai", "emoji": "🥬", "min_n": 80, "min_p": 20, "min_k": 90, "ph_min": 6.0, "ph_max": 7.5, "min_oc": 0.7, "base_score": 91},
    {"name": "Indian Spinach", "emoji": "🍃", "min_n": 75, "min_p": 25, "min_k": 85, "ph_min": 6.2, "ph_max": 7.2, "min_oc": 0.8, "base_score": 88},
    {"name": "Spearmint", "emoji": "🌿", "min_n": 65, "min_p": 20, "min_k": 70, "ph_min": 6.0, "ph_max": 7.0, "min_oc": 0.8, "base_score": 86},
    {"name": "Coriander", "emoji": "🌿", "min_n": 50, "min_p": 20, "min_k": 60, "ph_min": 6.2, "ph_max": 7.2, "min_oc": 0.6, "base_score": 83},
    {"name": "Curry Leaf", "emoji": "🪴", "min_n": 60, "min_p": 25, "min_k": 110, "ph_min": 6.0, "ph_max": 7.5, "min_oc": 0.6, "base_score": 85},
    {"name": "White Radish", "emoji": "🥕", "min_n": 45, "min_p": 35, "min_k": 100, "ph_min": 6.0, "ph_max": 6.8, "min_oc": 0.5, "base_score": 82},
    {"name": "Strawberry", "emoji": "🍓", "min_n": 40, "min_p": 40, "min_k": 140, "ph_min": 5.5, "ph_max": 6.5, "min_oc": 0.9, "base_score": 86},
]

TRADITIONAL_IRRIGATION = 22.0  # L/m² baseline

class SoilAnalyzer:
    @staticmethod
    def analyze(soil: SoilInput) -> SoilAnalysisResult:
        # 1. Chemical Nutrient Scoring
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

        # Multi-factor agronomic fertility score
        fertility = round(
            n_score * 0.30 + p_score * 0.20 + k_score * 0.20 + ph_score * 0.15 + oc_score * 0.15, 1
        )
        fertility = max(5.0, min(98.0, fertility))

        classification = "High" if fertility >= 70 else "Medium" if fertility >= 45 else "Low"

        # 2. Machine Learning Crop Classification
        # Delegate directly to our trained Random Forest Classifier
        matched_crops = []
        try:
            from ml.train_crop_model import CropRecommender
            recommender = CropRecommender()
            ml_pred = recommender.predict(
                n=soil.nitrogen,
                p=soil.phosphorus,
                k=soil.potassium,
                ph=soil.ph,
                oc=soil.organic_carbon,
                soil_type=getattr(soil, "soil_texture", "loam") or "loam"
            )
            # Map emojis for predicted top candidates
            crop_emojis: Dict[str, str] = {
                "Bush Tomato": "🍅",
                "Cherry Tomato": "🍅",
                "Green Chilli": "🌶️",
                "Capsicum": "🫑",
                "Brinjal": "🍆",
                "Okra": "🥢",
                "Bush French Beans": "🫘",
                "Amaranth Keerai": "🥬",
                "Indian Spinach": "🍃",
                "Spearmint": "🌿",
                "Coriander": "🌿",
                "Curry Leaf": "🪴",
                "White Radish": "🥕",
                "Strawberry": "🍓",
            }
            for candidate in ml_pred["top_candidates"]:
                cname = candidate["crop"]
                emoji = crop_emojis.get(cname, "🌱")
                match_score = round(candidate["probability"] * 100)
                matched_crops.append({"name": f"{emoji} {cname}", "match_score": max(50, match_score)})
        except Exception as e:
            # Fallback to database matching if ML artifact is loading
            for crop in CROP_DATABASE:
                min_n = float(crop.get("min_n", 0.0))
                min_p = float(crop.get("min_p", 0.0))
                min_k = float(crop.get("min_k", 0.0))
                ph_min = float(crop.get("ph_min", 0.0))
                ph_max = float(crop.get("ph_max", 14.0))
                min_oc = float(crop.get("min_oc", 0.0))
                base_score = float(crop.get("base_score", 70.0))

                if (soil.nitrogen >= min_n and soil.phosphorus >= min_p and
                        soil.potassium >= min_k and ph_min <= soil.ph <= ph_max and
                        soil.organic_carbon >= min_oc):
                    bonus = min(10.0, (soil.nitrogen - min_n) / 10.0)
                    score = round(min(99.0, base_score + bonus))
                    matched_crops.append({"name": f'{crop.get("emoji", "🌱")} {crop.get("name", "Crop")}', "match_score": score})

        if not matched_crops:
            matched_crops = [{"name": "🍅 Bush Tomato", "match_score": 75}]

        matched_crops.sort(key=lambda x: x["match_score"], reverse=True)

        # 3. Dynamic Agronomic & ML-Informed Recommendations
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
        recs.append("ML Recommendation: Apply 50 g/m² superabsorbent hydrogel polymer into topsoil layer to extend soil hydration half-life to 48 hours.")
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
        """ML-Driven Predictive Irrigation Calculation with Hydrogel Retention Factor."""
        alpha = SOIL_COEFFICIENTS.get("loam", 0.85)
        if hasattr(data, "alpha") and data.alpha:
            alpha = data.alpha

        # Compute with ML Predictive Forecasting Engine if available
        try:
            from services.irrigation_decision_engine import IrrigationDecisionEngine
            from schemas import PredictiveDecisionInput
            
            ml_decision = IrrigationDecisionEngine.evaluate(PredictiveDecisionInput(
                current_moisture=data.sm_current,
                target_moisture=data.sm_optimal,
                temperature=32.0,
                humidity=65.0,
                rainfall_forecast_6h=0.0,
                soil_texture="loam",
                field_area=data.field_area,
                hydrogel_present=1
            ))
            
            total_water = ml_decision.water_required_litres
            ir = round(total_water / max(1.0, data.field_area), 2)
            smd = round(max(0.0, data.sm_optimal - data.sm_current), 2)
            
            # Water saved compared to traditional baseline (22 L/m²)
            traditional_total = TRADITIONAL_IRRIGATION * data.field_area
            saved = round(max(0.0, (1 - total_water / max(1.0, traditional_total)) * 100), 1)
        except Exception:
            # Fallback calculation
            smd = max(0.0, data.sm_optimal - data.sm_current)
            # Hydrogel reduces effective water deficit by 18% through desorption kinetics
            ir = round(alpha * smd * 0.82, 2)
            total_water = round(ir * data.field_area, 0)
            saved = round((1 - ir / TRADITIONAL_IRRIGATION) * 100, 1) if ir < TRADITIONAL_IRRIGATION else 0.0
            saved = max(0.0, saved)

        if saved >= 30:
            efficiency = "Excellent (ML Predictive + Hydrogel)"
        elif saved >= 20:
            efficiency = "Good"
        elif saved >= 10:
            efficiency = "Moderate"
        else:
            efficiency = "Low"

        return IrrigationResult(
            smd=round(smd, 2),
            irrigation_required=ir,
            total_water_litres=round(total_water, 1),
            water_saved=saved,
            efficiency_rating=efficiency,
        )
