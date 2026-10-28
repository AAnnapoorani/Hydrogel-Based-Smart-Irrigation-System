"""Autonomous Closed-Loop Irrigation Automation Service for IRRIGATEWISE.

Orchestrates the autonomous cyber-physical loop:
  [ SENSE ]    -> Ingests ESP32 telemetry (soil moisture, temperature, humidity, wind)
  [ DETECT ]   -> Screens for sensor anomalies via ML Isolation Forest
  [ PREDICT ]  -> Forecasts soil moisture trajectory at t+1h, t+3h, t+6h horizons
  [ DECIDE ]   -> Evaluates ML predictive decision matrix (hydrogel desorption & rain offset)
  [ ACT ]      -> Automatically dispatches pump actuation pulse under safety interlocks
  [ VERIFY ]   -> Closed-loop feedback comparing predictions against ground-truth post-hoc readings
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session 

import models
from schemas import (
    SensorReadingCreate,
    PredictiveDecisionInput,
    PumpExecutionInput
)
from ml.anomaly_detection import check_sensor_anomaly
from ml.predict import SoilMoisturePredictor
from services.irrigation_decision_engine import IrrigationDecisionEngine
from services.pump_controller import PumpController
from services.feedback_service import FeedbackService

class AutomationService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutomationService, cls).__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self.autonomous_enabled = True
        self.auto_actuation_enabled = True
        self.simulation_mode = True
        self.target_moisture = 60.0
        self.field_area = 10.0  # 10 container grow bags
        self.pot_count = 10
        self.total_cycles_automated = 0
        self.total_water_managed_litres = 0.0
        self.total_water_managed_ml = 0.0
        self.last_cycle_timestamp: Optional[datetime] = None
        self.last_cycle_decision: Optional[Dict[str, Any]] = None
        self.recent_automation_events: List[Dict[str, Any]] = []

    def get_status(self) -> Dict[str, Any]:
        """Returns current operational status of the autonomous closed-loop system."""
        pump_ctrl = PumpController()
        pump_status = pump_ctrl.get_status()
        
        return {
            "autonomous_mode": "ACTIVE" if self.autonomous_enabled else "STANDBY",
            "autonomous_enabled": self.autonomous_enabled,
            "auto_actuation_enabled": self.auto_actuation_enabled,
            "simulation_mode": self.simulation_mode,
            "target_moisture": self.target_moisture,
            "field_area": self.field_area,
            "pot_count": self.pot_count,
            "environment": "Terrace Garden (Potted Grow Bags)",
            "irrigation_unit": "mL",
            "total_cycles_automated": self.total_cycles_automated,
            "total_water_managed_litres": round(self.total_water_managed_litres, 2),
            "total_water_managed_ml": round(self.total_water_managed_ml, 1),
            "last_cycle_timestamp": self.last_cycle_timestamp.isoformat() if self.last_cycle_timestamp else None,
            "last_cycle_decision": self.last_cycle_decision,
            "pump_state": pump_status["status"],
            "emergency_stop": pump_status["emergency_stop"],
            "recent_events": self.recent_automation_events[-10:]
        }

    def set_settings(
        self,
        autonomous_enabled: Optional[bool] = None,
        auto_actuation_enabled: Optional[bool] = None,
        simulation_mode: Optional[bool] = None,
        target_moisture: Optional[float] = None,
        field_area: Optional[float] = None
    ) -> Dict[str, Any]:
        """Updates automation operational parameters."""
        if autonomous_enabled is not None:
            self.autonomous_enabled = autonomous_enabled
        if auto_actuation_enabled is not None:
            self.auto_actuation_enabled = auto_actuation_enabled
        if simulation_mode is not None:
            self.simulation_mode = simulation_mode
            PumpController().simulation_mode = simulation_mode
        if target_moisture is not None:
            self.target_moisture = float(target_moisture)
        if field_area is not None:
            self.field_area = float(field_area)
            
        return self.get_status()

    def process_sensor_telemetry(
        self,
        payload: SensorReadingCreate,
        db: Session,
        prev_reading: Optional[models.SensorReading] = None,
        recent_history: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Main automated closed-loop entrypoint triggered on every sensor packet."""
        now = datetime.now(timezone.utc)
        results: Dict[str, Any] = {
            "autonomous_processed": False,
            "anomaly_detected": False,
            "forecast": None,
            "decision": None,
            "actuation": None,
            "feedback_verified": None
        }

        # ── 1. DETECT: ML Anomaly Screening ─────────────────────────────
        prev_m = prev_reading.soil_moisture if prev_reading else None
        anomaly_res = check_sensor_anomaly(
            soil_moisture=payload.soil_moisture,
            temperature=payload.temperature,
            humidity=payload.humidity,
            previous_moisture=prev_m,
            pump_status=payload.pump_status or "OFF",
            recent_history=recent_history
        )
        
        if anomaly_res["is_anomaly"]:
            results["anomaly_detected"] = True
            # In anomaly state, suppress automated irrigation to protect crop root zone
            event_log = {
                "timestamp": now.isoformat(),
                "type": "ANOMALY_SUPPRESSION",
                "message": f"Automation held: Sensor anomaly detected ({anomaly_res['anomaly_type']})",
                "severity": anomaly_res["severity"]
            }
            self.recent_automation_events.append(event_log)
            return results

        if not self.autonomous_enabled:
            return results

        # ── 2. PREDICT: ML Multi-Horizon Soil Moisture Forecasting ──────
        predictor = SoilMoisturePredictor()
        ml_input = PredictiveDecisionInput(
            current_moisture=payload.soil_moisture,
            target_moisture=self.target_moisture,
            temperature=payload.temperature,
            humidity=payload.humidity,
            rainfall_forecast_6h=payload.rainfall or 0.0,
            wind_speed=payload.wind_speed or 12.0,
            soil_texture=payload.soil_type or "cocopeat_mix",
            crop_type=payload.crop_type or "Potted Tomato",
            hydrogel_present=payload.hydrogel_present if payload.hydrogel_present is not None else 1,
            field_area=self.field_area,
            pot_count=self.pot_count,
            hours_since_irrigation=12.0
        )
        
        decision = IrrigationDecisionEngine.evaluate(ml_input)
        
        results["forecast"] = {
            "current": decision.current_moisture,
            "predicted_1h": decision.predicted_moisture_1h,
            "predicted_3h": decision.predicted_moisture_3h,
            "predicted_6h": decision.predicted_moisture_6h,
            "confidence": decision.confidence
        }
        results["decision"] = {
            "irrigation_required": decision.irrigation_required,
            "water_required_litres": decision.water_required_litres,
            "water_required_ml": decision.water_required_ml or round(decision.water_required_litres * 1000.0, 1),
            "water_per_pot_ml": decision.water_per_pot_ml or round((decision.water_required_litres * 1000.0) / max(1, self.pot_count), 1),
            "pot_count": self.pot_count,
            "irrigation_unit": "mL",
            "duration_minutes": decision.estimated_pump_duration_minutes,
            "reason": decision.reason,
            "water_saving_pct": decision.comparison.water_saving_advantage_pct
        }

        # ── 3. ACT: Automated Safe Actuation ────────────────────────────
        actuation_result = None
        if decision.irrigation_required and self.auto_actuation_enabled:
            pump_ctrl = PumpController()
            pump_ctrl.simulation_mode = self.simulation_mode
            
            actuation_exec = pump_ctrl.execute_irrigation(
                duration_minutes=decision.estimated_pump_duration_minutes,
                water_amount_litres=decision.water_required_litres,
                current_moisture=payload.soil_moisture,
                override_safety=False
            )
            
            actuation_result = actuation_exec
            if actuation_exec.get("success"):
                # Record to irrigation_events in database
                irr_event = models.IrrigationEvent(
                    decision_mode="ml_predictive_automated",
                    trigger_reason=f"[AUTONOMOUS AI] {decision.reason}",
                    water_amount_litres=decision.water_required_litres,
                    duration_minutes=actuation_exec["duration_minutes"],
                    status=actuation_exec["status"],
                    pump_id="PUMP_MAIN",
                    timestamp=now
                )
                db.add(irr_event)
                self.total_cycles_automated += 1
                self.total_water_managed_litres += decision.water_required_litres

        results["actuation"] = actuation_result
        self.last_cycle_timestamp = now
        self.last_cycle_decision = results["decision"]

        # ── 4. VERIFY: Closed-Loop Post-Hoc Prediction Feedback ─────────
        # Find predictions logged roughly 1 to 3 hours ago to verify accuracy
        time_1h_ago = now - timedelta(hours=1, minutes=15)
        time_1h_recent = now - timedelta(minutes=45)
        
        past_prediction = db.query(models.MLPrediction).filter(
            models.MLPrediction.timestamp >= time_1h_ago,
            models.MLPrediction.timestamp <= time_1h_recent
        ).order_by(models.MLPrediction.timestamp.asc()).first()
        
        if past_prediction:
            try:
                feedback = FeedbackService.record_feedback(
                    db=db,
                    predicted_moisture=past_prediction.predicted_1h,
                    actual_moisture=payload.soil_moisture,
                    horizon_hours=1,
                    prediction_id=past_prediction.id
                )
                results["feedback_verified"] = {
                    "horizon_hours": 1,
                    "predicted": past_prediction.predicted_1h,
                    "actual": payload.soil_moisture,
                    "absolute_error": feedback.absolute_error,
                    "error_pct": feedback.relative_error_pct
                }
            except Exception as e:
                print(f"[Automation Feedback] Verification error: {e}")

        # Log event summary
        status_msg = "Irrigation Pulse Dispatched" if (actuation_result and actuation_result.get("success")) else "Hydration Optimal"
        self.recent_automation_events.append({
            "timestamp": now.isoformat(),
            "type": "CYCLE_PROCESSED",
            "moisture": payload.soil_moisture,
            "predicted_3h": decision.predicted_moisture_3h,
            "decision": "IRRIGATE" if decision.irrigation_required else "HOLD",
            "status": status_msg
        })
        if len(self.recent_automation_events) > 50:
            self.recent_automation_events = self.recent_automation_events[-50:]

        results["autonomous_processed"] = True
        return results

def get_automation_service() -> AutomationService:
    return AutomationService()
