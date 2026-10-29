"""Unit Tests for Irrigation Decision Engine and Pump Controller."""

# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from services.irrigation_decision_engine import IrrigationDecisionEngine
# pyrefly: ignore [missing-import]
from services.pump_controller import PumpController
# pyrefly: ignore [missing-import]
from schemas import PredictiveDecisionInput

def test_decision_engine_mode_comparison():
    """Verifies that decision engine compares rule-based vs ML predictive modes."""
    inp = PredictiveDecisionInput(
        current_moisture=35.0,  # Below threshold
        target_moisture=65.0,
        temperature=32.0,
        humidity=60.0,
        rainfall_forecast_6h=0.0,
        soil_texture="loam",
        hydrogel_present=1,
        field_area=500.0
    )
    res = IrrigationDecisionEngine.evaluate(inp)
    
    assert res.irrigation_required is True
    assert res.water_required_litres > 0
    assert res.estimated_pump_duration_minutes > 0
    assert res.comparison is not None
    assert res.comparison.rule_based_decision is True
    assert res.comparison.ml_predictive_decision is True
    # Hydrogel presence should provide an efficiency water saving advantage
    assert res.comparison.water_difference_litres >= 0
    assert res.comparison.water_saving_advantage_pct >= 0

def test_rain_suppression_logic():
    """Verifies that heavy predicted rain holds back irrigation to conserve water."""
    inp = PredictiveDecisionInput(
        current_moisture=40.0,
        target_moisture=65.0,
        temperature=28.0,
        humidity=85.0,
        rainfall_forecast_6h=15.0,  # 15mm rain forecast
        soil_texture="loam",
        hydrogel_present=1,
        field_area=500.0
    )
    res = IrrigationDecisionEngine.evaluate(inp)
    assert res.irrigation_required is False
    assert "Rain forecast predicts" in res.reason or "suppressed" in res.reason

def test_pump_controller_safety_guards():
    """Verifies pump controller safety limits (max moisture, emergency stop)."""
    controller = PumpController()
    controller.reset_emergency_stop()
    
    # 1. High moisture safety ceiling
    res_high = controller.execute_irrigation(
        duration_minutes=15.0,
        water_amount_litres=2000.0,
        current_moisture=88.0  # Above 85% safety limit
    )
    assert res_high["success"] is False
    assert "Safety limit tripped" in res_high["message"]
    
    # 2. Emergency stop lock
    controller.emergency_stop()
    res_stop = controller.execute_irrigation(
        duration_minutes=10.0,
        water_amount_litres=1000.0,
        current_moisture=40.0
    )
    assert res_stop["success"] is False
    assert "Emergency stop is currently engaged" in res_stop["message"]
    
    controller.reset_emergency_stop()
