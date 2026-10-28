"""Predictive Irrigation and Actuation Router for IRRIGATEWISE.

Handles:
- Hybrid rule-based vs ML predictive decision evaluation
- Safe pump actuation (simulation and hardware modes)
- Actuation event logging
- Closed-loop prediction feedback
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from database import get_db
import models
import schemas
from services.irrigation_decision_engine import IrrigationDecisionEngine
from services.pump_controller import PumpController
from services.feedback_service import FeedbackService

router = APIRouter(prefix="/irrigation", tags=["Irrigation & Automation"])

@router.post("/predict", response_model=schemas.PredictiveDecisionOutput)
def evaluate_predictive_irrigation(
    payload: schemas.PredictiveDecisionInput,
    db: Session = Depends(get_db)
):
    """Evaluates soil conditions, predicts future moisture, and determines irrigation requirements

    comparing Traditional Rule-Based SMD against ML-Based Predictive Decision.
    """
    decision = IrrigationDecisionEngine.evaluate(payload)
    return decision

@router.post("/execute", response_model=schemas.PumpExecutionOutput)
def execute_pump_actuation(
    payload: schemas.PumpExecutionInput,
    db: Session = Depends(get_db)
):
    """Activates irrigation pump (in simulation or hardware mode) with strict safety bounds."""
    controller = PumpController()
    controller.simulation_mode = payload.simulation_mode
    
    # Check latest moisture reading for safety
    latest_reading = db.query(models.SensorReading).order_by(
        models.SensorReading.timestamp.desc()
    ).first()
    curr_m = float(latest_reading.soil_moisture) if latest_reading else 40.0
    
    actuation = controller.execute_irrigation(
        duration_minutes=payload.duration_minutes,
        water_amount_litres=payload.water_amount_litres,
        current_moisture=curr_m
    )
    
    if not actuation["success"]:
        raise HTTPException(status_code=400, detail=actuation["message"])
        
    # Log event into irrigation_events table
    event = models.IrrigationEvent(
        decision_mode=payload.decision_mode,
        trigger_reason=payload.trigger_reason,
        water_amount_litres=payload.water_amount_litres,
        duration_minutes=actuation["duration_minutes"],
        status=actuation["status"],
        pump_id="PUMP_MAIN",
        timestamp=datetime.now(timezone.utc)
    )
    db.add(event)
    db.commit()
    
    return schemas.PumpExecutionOutput(
        status=actuation["status"],
        pump_state=actuation["pump_state"],
        mode="SIMULATION" if payload.simulation_mode else "HARDWARE",
        duration_minutes=actuation["duration_minutes"],
        water_amount_litres=payload.water_amount_litres,
        timestamp=datetime.now(timezone.utc),
        message=actuation["message"]
    )

@router.get("/pump-status")
def get_pump_status():
    """Returns the operational status, cooldown counters, and safety locks of the pump."""
    controller = PumpController()
    return controller.get_status()

@router.get("/decision-history")
def get_irrigation_history(limit: int = 30, db: Session = Depends(get_db)):
    """Returns past irrigation events and water consumption."""
    events = db.query(models.IrrigationEvent).order_by(
        models.IrrigationEvent.timestamp.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": e.id,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "decision_mode": e.decision_mode,
            "trigger_reason": e.trigger_reason,
            "water_amount_litres": e.water_amount_litres,
            "duration_minutes": e.duration_minutes,
            "status": e.status,
            "pump_id": e.pump_id
        }
        for e in events
    ]

@router.post("/feedback", response_model=schemas.FeedbackOut)
def record_prediction_feedback(
    payload: schemas.FeedbackCreate,
    db: Session = Depends(get_db)
):
    """Records ground-truth observed moisture after prediction horizon to track accuracy."""
    entry = FeedbackService.record_feedback(
        db=db,
        predicted_moisture=payload.predicted_moisture,
        actual_moisture=payload.actual_moisture,
        horizon_hours=payload.horizon_hours,
        prediction_id=payload.prediction_id
    )
    return entry

@router.get("/feedback")
def get_prediction_feedback_analytics(db: Session = Depends(get_db)):
    """Returns model residual error analytics and prediction accuracy over time."""
    return FeedbackService.get_feedback_analytics(db)

# ── Autonomous Closed-Loop Automation Endpoints ─────────────────────

@router.get("/automation/status")
def get_automation_status():
    """Returns real-time status of the autonomous closed-loop predictive engine."""
    from services.automation_service import AutomationService
    return AutomationService().get_status()

@router.post("/automation/toggle")
def toggle_automation(
    autonomous_enabled: Optional[bool] = None,
    auto_actuation_enabled: Optional[bool] = None,
    simulation_mode: Optional[bool] = None,
    target_moisture: Optional[float] = None
):
    """Enables or disables autonomous closed-loop operation and configures thresholds."""
    from services.automation_service import AutomationService
    automation = AutomationService()
    return automation.set_settings(
        autonomous_enabled=autonomous_enabled,
        auto_actuation_enabled=auto_actuation_enabled,
        simulation_mode=simulation_mode,
        target_moisture=target_moisture
    )

@router.post("/automation/trigger-cycle")
def trigger_autonomous_cycle(db: Session = Depends(get_db)):
    """Manually triggers an autonomous ML evaluation and actuation cycle on latest telemetry."""
    from services.automation_service import AutomationService
    from schemas import SensorReadingCreate
    
    latest_reading = db.query(models.SensorReading).order_by(
        models.SensorReading.timestamp.desc()
    ).first()
    
    if not latest_reading:
        raise HTTPException(status_code=404, detail="No sensor telemetry available to evaluate.")
        
    payload = SensorReadingCreate(
        device_id=str(latest_reading.device_id or "ESP32_FIELD_01"),
        soil_moisture=float(latest_reading.soil_moisture),
        temperature=float(latest_reading.temperature),
        humidity=float(latest_reading.humidity),
        rainfall=float(latest_reading.rainfall) if latest_reading.rainfall is not None else 0.0,
        wind_speed=float(latest_reading.wind_speed) if latest_reading.wind_speed is not None else 0.0,
        soil_type=str(latest_reading.soil_type or "loam"),
        crop_type=str(latest_reading.crop_type or "Samba Rice"),
        hydrogel_present=int(latest_reading.hydrogel_present) if latest_reading.hydrogel_present is not None else 1,
        hydrogel_dosage=float(latest_reading.hydrogel_dosage) if latest_reading.hydrogel_dosage is not None else 50.0,
        pump_status=str(latest_reading.pump_status or "OFF")
    )
    
    automation = AutomationService()
    res = automation.process_sensor_telemetry(payload=payload, db=db)
    return {
        "success": True,
        "message": "Autonomous ML evaluation cycle completed successfully.",
        "cycle_results": res
    }

