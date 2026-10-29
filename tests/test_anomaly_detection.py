"""Unit Tests for Sensor Anomaly Detection Engine."""

# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
try:
    from backend.ml.anomaly_detection import check_sensor_anomaly
except ModuleNotFoundError:
    from ml.anomaly_detection import check_sensor_anomaly

def test_impossible_moisture_detection():
    """Detects physically impossible moisture readings (e.g. >100% or <0%)."""
    res1 = check_sensor_anomaly(soil_moisture=125.0, temperature=30.0, humidity=70.0)
    assert res1["is_anomaly"] is True
    assert res1["anomaly_type"] == "impossible_moisture_value"
    assert res1["severity"] == "CRITICAL"

    res2 = check_sensor_anomaly(soil_moisture=-5.0, temperature=30.0, humidity=70.0)
    assert res2["is_anomaly"] is True
    assert res2["anomaly_type"] == "impossible_moisture_value"

def test_sudden_spike_detection():
    """Detects physically abnormal instantaneous jumps."""
    res = check_sensor_anomaly(
        soil_moisture=88.0,
        temperature=32.0,
        humidity=65.0,
        previous_moisture=38.0,  # 50% jump in 1 cycle
        pump_status="OFF"
    )
    assert res["is_anomaly"] is True
    assert res["anomaly_type"] == "sudden_spike"

def test_sensor_freeze_detection():
    """Detects flatlined ADC / dead sensor signal."""
    history = [52.4, 52.4, 52.4, 52.4, 52.4, 52.4]
    res = check_sensor_anomaly(
        soil_moisture=52.4,
        temperature=30.0,
        humidity=70.0,
        previous_moisture=52.4,
        recent_history=history
    )
    assert res["is_anomaly"] is True
    assert res["anomaly_type"] == "sensor_freeze"

def test_pump_decoupling_detection():
    """Detects when pump is ON but no moisture increases."""
    res = check_sensor_anomaly(
        soil_moisture=35.0,
        temperature=32.0,
        humidity=60.0,
        previous_moisture=35.0,
        pump_status="ON"
    )
    assert res["is_anomaly"] is True
    assert res["anomaly_type"] == "pump_no_response"
