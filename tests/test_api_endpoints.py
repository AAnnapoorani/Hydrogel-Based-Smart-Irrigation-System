"""Integration Tests for FastAPI Endpoints using ASGITransport."""

# pyrefly: ignore [missing-import]
import pytest
import asyncio
# pyrefly: ignore [missing-import]
import httpx
# pyrefly: ignore [missing-import]
from main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

async def get_client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")

@pytest.mark.anyio
async def test_health_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"

@pytest.mark.anyio
async def test_soil_analyze_legacy_endpoint():
    payload = {
        "nitrogen": 85.0,
        "phosphorus": 42.0,
        "potassium": 210.0,
        "ph": 6.8,
        "organic_carbon": 0.82,
        "soil_texture": "loam"
    }
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/soil/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "fertility_score" in data
        assert data["classification"] in ["High", "Medium", "Low"]
        assert len(data["recommended_crops"]) > 0

@pytest.mark.anyio
async def test_sensor_ingestion_api():
    payload = {
        "device_id": "ESP32_TEST_01",
        "soil_moisture": 54.2,
        "temperature": 31.5,
        "humidity": 68.0,
        "rainfall": 0.0,
        "wind_speed": 12.0,
        "soil_type": "loam",
        "crop_type": "Samba Rice",
        "hydrogel_present": 1,
        "hydrogel_dosage": 50.0,
        "pump_status": "OFF"
    }
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/sensors/readings", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["soil_moisture"] == 54.2
        assert data["device_id"] == "ESP32_TEST_01"

@pytest.mark.anyio
async def test_moisture_predict_api():
    payload = {
        "current_moisture": 40.0,
        "temperature": 32.0,
        "humidity": 65.0,
        "rainfall": 0.0,
        "wind_speed": 10.0,
        "soil_type": "loam",
        "crop_type": "Samba Rice",
        "hydrogel_present": 1,
        "hours_since_irrigation": 14.0,
        "target_moisture": 65.0
    }
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/ml/moisture/predict", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "predicted_1h" in data
        assert "predicted_3h" in data
        assert "predicted_6h" in data
        assert "model_name" in data

@pytest.mark.anyio
async def test_crop_predict_ml_api():
    payload = {
        "nitrogen": 90.0,
        "phosphorus": 45.0,
        "potassium": 210.0,
        "ph": 6.8,
        "organic_carbon": 0.85,
        "temperature": 30.0,
        "humidity": 75.0,
        "rainfall": 150.0,
        "soil_type": "loam"
    }
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/ml/crop/predict", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "recommended_crop" in data
        assert "confidence" in data
        assert len(data["top_candidates"]) > 0

@pytest.mark.anyio
async def test_irrigation_predict_api():
    payload = {
        "current_moisture": 36.0,
        "target_moisture": 65.0,
        "temperature": 33.0,
        "humidity": 60.0,
        "rainfall_forecast_6h": 0.0,
        "soil_texture": "loam",
        "crop_type": "Samba Rice",
        "hydrogel_present": 1,
        "field_area": 500.0
    }
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/irrigation/predict", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "irrigation_required" in data
        assert "comparison" in data
        assert "rule_based_decision" in data["comparison"]
        assert "ml_predictive_decision" in data["comparison"]

@pytest.mark.anyio
async def test_model_evaluation_metrics_api():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/ml/evaluation")
        assert res.status_code == 200
        data = res.json()
        assert "models" in data
        assert len(data["models"]) >= 3
        assert "best_model" in data

@pytest.mark.anyio
async def test_reports_summary_api():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/reports/summary")
        assert res.status_code == 200
        data = res.json()
        assert "total_soil_records" in data
        assert "average_water_saved_pct" in data

@pytest.mark.anyio
async def test_metrics_comparison_api():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/ml/metrics-comparison")
        assert res.status_code == 200
        data = res.json()
        assert "models_comparison" in data
        assert "operational_comparison" in data
        assert "crop_confusion_matrix" in data
        assert "anomaly_comparison" in data
        assert "trajectory_72h" in data
        assert "diurnal_water_heatmap" in data
        assert len(data["models_comparison"]) >= 4
        assert data["crop_confusion_matrix"]["overall_accuracy"] >= 0.85

@pytest.mark.anyio
async def test_automation_status_and_cycle_api():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/irrigation/automation/status")
        assert res.status_code == 200
        data = res.json()
        assert "autonomous_mode" in data
        assert "auto_actuation_enabled" in data
        
        # Test toggle
        toggle_res = await client.post("/api/v1/irrigation/automation/toggle?autonomous_enabled=true&auto_actuation_enabled=true")
        assert toggle_res.status_code == 200
        toggle_data = toggle_res.json()
        assert toggle_data["autonomous_enabled"] is True

@pytest.mark.anyio
async def test_node_status_and_heartbeat_api():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Check initial node status
        res = await client.get("/api/v1/sensors/node-status")
        assert res.status_code == 200
        status_data = res.json()
        assert "is_online" in status_data
        assert "status" in status_data
        assert "status_label" in status_data
        assert "signal_strength" in status_data
        assert "message" in status_data

        # Post a heartbeat and verify it acknowledges and marks online
        hb_payload = {
            "device_id": "ESP32_FIELD_01",
            "firmware_version": "v2.1",
            "rssi_dbm": -55,
            "battery_level_pct": 98.0
        }
        hb_res = await client.post("/api/v1/sensors/heartbeat", json=hb_payload)
        assert hb_res.status_code == 200
        hb_data = hb_res.json()
        assert hb_data["is_online"] is True
        assert hb_data["status"] == "acknowledged"

        # Verify node-status now reports online with EXCELLENT signal
        status_res2 = await client.get("/api/v1/sensors/node-status")
        assert status_res2.status_code == 200
        status_data2 = status_res2.json()
        assert status_data2["is_online"] is True
        assert status_data2["status"] == "ONLINE"
        assert status_data2["signal_strength"] == "EXCELLENT"
        assert status_data2["battery_level_pct"] == 98.0

        # Also test simulate-packet endpoint
        sim_res = await client.post("/api/v1/sensors/simulate-packet")
        assert sim_res.status_code == 200
        sim_data = sim_res.json()
        assert "soil_moisture" in sim_data
        assert sim_data["is_online"] is True

        # Test back switch: disconnect endpoint immediately sets to OFFLINE
        disc_res = await client.post("/api/v1/sensors/disconnect")
        assert disc_res.status_code == 200
        disc_data = disc_res.json()
        assert disc_data["is_online"] is False
        assert disc_data["status"] == "OFFLINE"
        assert disc_data["status_label"] == "ESP32 Offline (Disconnected)"

        # Verify node-status now reports offline immediately
        status_res3 = await client.get("/api/v1/sensors/node-status")
        assert status_res3.status_code == 200
        assert status_res3.json()["is_online"] is False

        # Test toggle endpoint: toggle back to online
        toggle_on = await client.post("/api/v1/sensors/toggle-connection?connect=true")
        assert toggle_on.status_code == 200
        assert toggle_on.json()["is_online"] is True

        # Toggle back to offline
        toggle_off = await client.post("/api/v1/sensors/toggle-connection?connect=false")
        assert toggle_off.status_code == 200
        assert toggle_off.json()["is_online"] is False



