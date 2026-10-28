"""Weather API Router for IRRIGATEWISE.

Exposes endpoints for live Erumaiyur / Tambaram weather,
7-day forecasts, and rain suppression status.
"""

from fastapi import APIRouter, Query
from typing import Dict, Any

from services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["Live Weather (Open-Meteo)"])

@router.get("/current")
def get_current_weather(refresh: bool = Query(False, description="Force bypass in-memory cache")):
    """Returns live weather metrics for Erumaiyur Village, Tambaram, Tamil Nadu."""
    return WeatherService.get_current_weather(force_refresh=refresh)

@router.get("/forecast")
def get_weather_forecast():
    """Returns 7-day meteorological forecast and precipitation trends."""
    data = WeatherService.get_current_weather()
    return {
        "location": data["location"],
        "coordinates": data["coordinates"],
        "daily_7day": data["daily_7day"],
        "hourly_next_12h": data["hourly_next_12h"],
        "forecast_24h": data["forecast_24h"]
    }

@router.get("/alerts")
def get_weather_alerts():
    """Returns weather alerts and rain suppression recommendations for irrigation."""
    data = WeatherService.get_current_weather()
    fc_24h = data.get("forecast_24h", {})
    return {
        "rain_suppression_active": fc_24h.get("rain_suppression_recommended", False),
        "total_precipitation_mm_24h": fc_24h.get("total_precipitation_mm", 0.0),
        "max_rain_probability": fc_24h.get("max_rain_probability", 0),
        "alert_message": fc_24h.get("alert_message", "Normal conditions"),
        "timestamp": data.get("timestamp")
    }
