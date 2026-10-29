"""Automated Test Suite for Next-Level Upgrades:
1. Open-Meteo Live Weather API integration & rain suppression
2. WebSocket Telemetry & Stream Manager
"""

import pytest
import httpx
from main import app
from database import SessionLocal
from services.weather_service import WeatherService
from services.websocket_manager import ws_manager

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_live_weather_service():
    """Verifies Open-Meteo weather service returns structured forecasts."""
    weather = WeatherService.get_current_weather()
    assert "current" in weather
    assert "forecast_24h" in weather
    assert "daily_7day" in weather
    assert "location" in weather
    assert "Tambaram" in weather["location"]
    assert weather["current"]["temperature"] > 0
    assert len(weather["daily_7day"]) == 7

@pytest.mark.anyio
async def test_weather_api_endpoints():
    """Verifies FastAPI weather endpoints."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        res = await client.get("/api/v1/weather/current")
        assert res.status_code == 200
        data = res.json()
        assert "current" in data
        assert "temperature" in data["current"]

        res_alerts = await client.get("/api/v1/weather/alerts")
        assert res_alerts.status_code == 200
        alerts = res_alerts.json()
        assert "rain_suppression_active" in alerts
        assert "alert_message" in alerts

@pytest.mark.anyio
async def test_websocket_manager_singleton():
    """Verifies WebSocketManager connection and broadcast mechanics."""
    assert ws_manager is not None
    # Test sync broadcast without crash even with 0 clients
    ws_manager.broadcast_sync("TEST_EVENT", {"test": "data"})
    assert True
