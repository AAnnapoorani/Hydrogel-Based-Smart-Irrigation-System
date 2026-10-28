"""Predictive Irrigation Decision Engine for IRRIGATEWISE.

Integrates:
- Real-time soil moisture telemetry
- ML forecasted future soil moisture trajectory (1h, 3h, 6h)
- Superabsorbent hydrogel moisture buffering kinetics
- Short-term precipitation forecasts
- Crop water requirement and soil texture coefficients
- Traditional / Rule-Based SMD calculation as a direct comparative baseline
"""

import math
from typing import Dict, Any
from schemas import (
    PredictiveDecisionInput,
    PredictiveDecisionOutput,
    DecisionComparison,
    MoisturePredictionInput
)
from ml.predict import SoilMoisturePredictor
from logic import SOIL_COEFFICIENTS, TRADITIONAL_IRRIGATION
try:
    from config import (
        POTTING_MEDIUM_COEFFICIENTS,
        MOISTURE_THRESHOLDS,
        ENVIRONMENT,
        PUMP_FLOW_RATE_TOTAL_ML_PER_MIN
    )
except ImportError:
    POTTING_MEDIUM_COEFFICIENTS = SOIL_COEFFICIENTS
    MOISTURE_THRESHOLDS = {
        "optimal_target": 60.0,
        "critical_wilting_hydrogel": 38.0,
        "critical_wilting_control": 42.0,
        "deficit_trigger_margin": 12.0
    }
    ENVIRONMENT = {"pot_count": 10, "container_volume_litres": 15.0}
    PUMP_FLOW_RATE_TOTAL_ML_PER_MIN = 2000.0

SPECIES_OPTIMAL_MOISTURE = {
    "tomato": 58.0,
    "potted tomato": 58.0,
    "chili": 52.0,
    "mint": 65.0,
    "mint (pudina)": 65.0,
    "spinach": 62.0,
    "spinach (palak)": 62.0,
    "tulsi": 50.0,
    "tulsi (holy basil)": 50.0,
    "brinjal": 56.0,
    "brinjal (eggplant)": 56.0,
    "snake plant": 38.0,
    "rose": 54.0,
    "coriander": 60.0,
}

class IrrigationDecisionEngine:
    @staticmethod
    def evaluate(input_data: PredictiveDecisionInput) -> PredictiveDecisionOutput:
        curr_m = float(input_data.current_moisture)
        crop_key = (input_data.crop_type or "").lower().strip()
        default_target = SPECIES_OPTIMAL_MOISTURE.get(crop_key, MOISTURE_THRESHOLDS.get("optimal_target", 60.0))
        target_m = float(input_data.target_moisture if (input_data.target_moisture and input_data.target_moisture != 60.0) else default_target)
        area = float(input_data.field_area if input_data.field_area is not None else 10.0)
        
        # Detect container/terrace environment (area <= 50 or pot_count specified)
        is_terrace_container = area <= 50.0 or (input_data.pot_count is not None and input_data.pot_count > 0)
        pot_count = int(input_data.pot_count or (int(area) if area <= 50.0 else ENVIRONMENT.get("pot_count", 10)))
        
        if input_data.rainfall_forecast_6h is not None:
            rain_fc = float(input_data.rainfall_forecast_6h)
        else:
            try:
                from services.weather_service import WeatherService
                w_data = WeatherService.get_current_weather()
                rain_fc = float(w_data.get("forecast_24h", {}).get("total_precipitation_mm", 0.0))
            except Exception:
                rain_fc = 0.0
                
        raw_tex = (input_data.soil_texture or "cocopeat_mix").lower()
        alpha = POTTING_MEDIUM_COEFFICIENTS.get(raw_tex, SOIL_COEFFICIENTS.get(raw_tex, 0.75 if is_terrace_container else 0.85))
        hydrogel = input_data.hydrogel_present if input_data.hydrogel_present is not None else 1
        
        # ─────────────────────────────────────────────────────────────
        # 1. THRESHOLDS: Container Potting Medium vs. Field Soil
        # ─────────────────────────────────────────────────────────────
        if is_terrace_container:
            # Potting medium (cocopeat + compost) has high porosity and lower critical stress point
            critical_threshold = MOISTURE_THRESHOLDS.get("critical_wilting_hydrogel", 38.0) if hydrogel else MOISTURE_THRESHOLDS.get("critical_wilting_control", 42.0)
            trigger_smd_threshold = MOISTURE_THRESHOLDS.get("deficit_trigger_margin", 12.0)
        else:
            critical_threshold = 46.0 if hydrogel else 48.0
            trigger_smd_threshold = 18.0
        
        # ─────────────────────────────────────────────────────────────
        # 2. MODE 1: BASELINE TRADITIONAL / RULE-BASED CALCULATION
        # ─────────────────────────────────────────────────────────────
        rule_smd = max(0.0, target_m - curr_m)
        rule_irr_required = curr_m < critical_threshold or rule_smd >= trigger_smd_threshold
        
        if rule_irr_required:
            if is_terrace_container:
                # In 15L terrace pots: SMD% deficit translates to mL per pot
                # Standard container water deficit factor (~25-30 mL per 1% SMD for 15L mix)
                rule_water_per_pot_ml = round(alpha * rule_smd * 28.0, 1)
                rule_water_total_ml = round(rule_water_per_pot_ml * pot_count, 1)
                rule_water_total = round(rule_water_total_ml / 1000.0, 2)
            else:
                rule_ir_rate = round(alpha * rule_smd, 2)  # L/m²
                rule_water_total = round(rule_ir_rate * area, 1)
                rule_water_total_ml = round(rule_water_total * 1000.0, 1)
                rule_water_per_pot_ml = round(rule_water_total_ml / max(1, pot_count), 1)
        else:
            rule_water_total = 0.0
            rule_water_total_ml = 0.0
            rule_water_per_pot_ml = 0.0

        # ─────────────────────────────────────────────────────────────
        # 3. MODE 2: ML PREDICTIVE FORECASTING
        # ─────────────────────────────────────────────────────────────
        predictor = SoilMoisturePredictor()
        ml_input = MoisturePredictionInput(
            current_moisture=curr_m,
            temperature=input_data.temperature,
            humidity=input_data.humidity,
            wind_speed=input_data.wind_speed or 10.0,
            soil_type=raw_tex if raw_tex in ["loam", "clay", "sandy", "silt"] else "loam",
            crop_type=input_data.crop_type or "Potted Tomato",
            hydrogel_present=hydrogel,
            hours_since_irrigation=input_data.hours_since_irrigation or 12.0,
            target_moisture=target_m
        )
        prediction = predictor.predict(ml_input)
        
        pred_1h = prediction.predicted_1h
        pred_3h = prediction.predicted_3h
        pred_6h = prediction.predicted_6h
        confidence = prediction.confidence_score
        
        # Predictive Decision Heuristics:
        # A) Rain Suppression: In a terrace garden, rainfall replenishes open grow bags
        rain_suppression = rain_fc >= (5.0 if is_terrace_container else 8.0)
        
        # B) Anticipatory Stress: Will moisture drop below critical within 3h or 6h?
        will_breach_in_3h = pred_3h < critical_threshold
        will_breach_in_6h = pred_6h < (critical_threshold - 2.0)
        currently_stressed = curr_m < critical_threshold
        
        ml_irr_required = False
        reason = ""
        ml_water_total = 0.0
        ml_water_total_ml = 0.0
        ml_water_per_pot_ml = 0.0
        
        if rain_suppression:
            ml_irr_required = False
            reason = f"Irrigation suppressed: Rain forecast predicts {rain_fc:.1f} mm in next 6 hours, naturally hydrating terrace grow bags."
        elif currently_stressed or will_breach_in_3h:
            ml_irr_required = True
            forecast_deficit = max(0.0, target_m - min(curr_m, pred_3h))
            
            # Hydrogel efficiency factor: Hydrogel retains water longer in container mix
            hg_discount = 0.80 if hydrogel else 1.0
            
            # Rain discount
            rain_offset = min(forecast_deficit * 0.4, rain_fc * 0.5)
            effective_deficit = max(3.0, (forecast_deficit - rain_offset) * hg_discount)
            
            if is_terrace_container:
                ml_water_per_pot_ml = round(alpha * effective_deficit * 24.0, 1)
                ml_water_total_ml = round(ml_water_per_pot_ml * pot_count, 1)
                ml_water_total = round(ml_water_total_ml / 1000.0, 2)
            else:
                ml_ir_rate = round(alpha * effective_deficit, 2)
                ml_water_total = round(ml_ir_rate * area, 1)
                ml_water_total_ml = round(ml_water_total * 1000.0, 1)
                ml_water_per_pot_ml = round(ml_water_total_ml / max(1, pot_count), 1)
            
            if currently_stressed:
                reason = f"Immediate deficit: Potting medium moisture ({curr_m}%) below critical threshold ({critical_threshold}%). Prescribed {ml_water_per_pot_ml} mL/pot."
            else:
                reason = f"Anticipatory deficit: Moisture projected to reach {pred_3h}% in 3 hours. Scheduled preemptive micro-drip pulse ({ml_water_per_pot_ml} mL/pot)."
        elif will_breach_in_6h and not hydrogel:
            # Container potting soil without hydrogel dries rapidly under terrace solar radiation
            ml_irr_required = True
            effective_deficit = max(2.5, (target_m - pred_6h) * 0.70)
            
            if is_terrace_container:
                ml_water_per_pot_ml = round(alpha * effective_deficit * 22.0, 1)
                ml_water_total_ml = round(ml_water_per_pot_ml * pot_count, 1)
                ml_water_total = round(ml_water_total_ml / 1000.0, 2)
            else:
                ml_ir_rate = round(alpha * effective_deficit, 2)
                ml_water_total = round(ml_ir_rate * area, 1)
                ml_water_total_ml = round(ml_water_total * 1000.0, 1)
                ml_water_per_pot_ml = round(ml_water_total_ml / max(1, pot_count), 1)
            reason = f"Proactive scheduling: Control potting medium without hydrogel projected to breach threshold in 6 hours ({pred_6h}%)."
        else:
            ml_irr_required = False
            if hydrogel:
                reason = f"Potting medium adequately hydrated: Hydrogel matrix buffering container moisture (predicted 3h: {pred_3h}%, 6h: {pred_6h}%). Zero irrigation required."
            else:
                reason = f"Container moisture satisfactory: Predicted 3h is {pred_3h}%. Monitoring ongoing."

        # Compute estimated pump duration (terrace mini-drip pump ~2,000 mL/min vs field 25 L/min)
        if is_terrace_container:
            pump_duration = round(ml_water_total_ml / PUMP_FLOW_RATE_TOTAL_ML_PER_MIN, 2) if ml_irr_required else 0.0
        else:
            pump_flow_lpm = max(10.0, area * 0.05)
            pump_duration = round(ml_water_total / pump_flow_lpm, 1) if ml_irr_required else 0.0

        # ─────────────────────────────────────────────────────────────
        # 4. COMPARATIVE BENCHMARK (RULE vs ML)
        # ─────────────────────────────────────────────────────────────
        water_diff = round(rule_water_total - ml_water_total, 2)
        water_diff_ml = round(rule_water_total_ml - ml_water_total_ml, 1)
        
        if rule_water_total > 0:
            saving_pct = round((water_diff / rule_water_total) * 100, 1)
        else:
            saving_pct = 0.0

        comparison = DecisionComparison(
            rule_based_decision=rule_irr_required,
            rule_based_water_litres=rule_water_total,
            rule_based_water_ml=rule_water_total_ml,
            rule_based_smd=round(rule_smd, 1),
            ml_predictive_decision=ml_irr_required,
            ml_predictive_water_litres=ml_water_total,
            ml_predictive_water_ml=ml_water_total_ml,
            predicted_moisture_3h=pred_3h,
            predicted_moisture_6h=pred_6h,
            water_difference_litres=water_diff,
            water_difference_ml=water_diff_ml,
            water_saving_advantage_pct=saving_pct,
            water_per_pot_ml=ml_water_per_pot_ml if ml_irr_required else 0.0
        )

        return PredictiveDecisionOutput(
            current_moisture=curr_m,
            predicted_moisture_1h=pred_1h,
            predicted_moisture_3h=pred_3h,
            predicted_moisture_6h=pred_6h,
            target_moisture=target_m,
            irrigation_required=ml_irr_required,
            water_required_litres=ml_water_total,
            water_required_ml=ml_water_total_ml,
            water_per_pot_ml=ml_water_per_pot_ml if ml_irr_required else 0.0,
            pot_count=pot_count,
            irrigation_unit="mL",
            estimated_pump_duration_minutes=pump_duration,
            decision_mode="ml_predictive",
            confidence=confidence,
            reason=reason,
            hydrogel_buffering_active=bool(hydrogel),
            comparison=comparison
        )

def evaluate_irrigation_decision(data: PredictiveDecisionInput) -> PredictiveDecisionOutput:
    return IrrigationDecisionEngine.evaluate(data)
