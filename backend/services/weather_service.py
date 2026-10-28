"""Live Weather Integration Service for IRRIGATEWISE.

Connects to Open-Meteo Global Meteorological API locked to the GPS coordinates
of Erumaiyur Village / Tambaram, Tamil Nadu (Lat: 12.9249° N, Lon: 80.1000° E).

Provides:
- Real-time live temperature, humidity, apparent temperature, and wind speed.
- Dynamic 24-hour and 7-day quantitative precipitation forecast (QPF).
- Reference Evapotranspiration (ET0) estimation.
- Rain suppression alerts for the predictive irrigation decision engine.
- Resilient in-memory caching (15-min TTL) with graceful regional fallback.
"""

import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

# GPS Coordinates for Tambaram Terrace Research Station, Tamil Nadu
ERUMAIYUR_LATITUDE = 12.9249
ERUMAIYUR_LONGITUDE = 80.1000
LOCATION_NAME = "Tambaram Terrace Research Station, Tamil Nadu"

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO Weather interpretation codes
WMO_CODE_MAP = {
    0: ("Clear sky", "☀️", "Clear"),
    1: ("Mainly clear", "🌤️", "Clear"),
    2: ("Partly cloudy", "⛅", "Cloudy"),
    3: ("Overcast", "☁️", "Overcast"),
    45: ("Foggy", "🌫️", "Fog"),
    48: ("Depositing rime fog", "🌫️", "Fog"),
    51: ("Light drizzle", "🌦️", "Drizzle"),
    53: ("Moderate drizzle", "🌦️", "Drizzle"),
    55: ("Dense drizzle", "🌧️", "Drizzle"),
    61: ("Slight rain", "🌧️", "Rain"),
    63: ("Moderate rain", "🌧️", "Rain"),
    65: ("Heavy rain", "⛈️", "Heavy Rain"),
    80: ("Slight rain showers", "🌦️", "Showers"),
    81: ("Moderate rain showers", "🌧️", "Showers"),
    82: ("Violent rain showers", "⛈️", "Torrential"),
    95: ("Thunderstorm", "⚡", "Thunderstorm"),
}

class WeatherService:
    _cache: Optional[Dict[str, Any]] = None
    _cache_time: float = 0.0
    _CACHE_TTL_SECONDS: int = 900  # 15 minutes

    @classmethod
    def get_current_weather(cls, force_refresh: bool = False) -> Dict[str, Any]:
        """Returns live weather metrics for Erumaiyur Village with caching."""
        now = time.time()
        if not force_refresh and cls._cache and (now - cls._cache_time < cls._CACHE_TTL_SECONDS):
            return cls._cache

        try:
            params = {
                "latitude": ERUMAIYUR_LATITUDE,
                "longitude": ERUMAIYUR_LONGITUDE,
                "current": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "surface_pressure"
                ],
                "hourly": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "precipitation_probability",
                    "precipitation",
                    "et0_fao_evapotranspiration"
                ],
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "weather_code"
                ],
                "timezone": "Asia/Kolkata",
                "forecast_days": 7
            }
            resp = requests.get(OPEN_METEO_URL, params=params, timeout=5.0)
            if resp.status_code == 200:
                raw = resp.json()
                processed = cls._process_weather_payload(raw)
                cls._cache = processed
                cls._cache_time = now
                return processed
        except Exception as e:
            print(f"WeatherService Warning: Live Open-Meteo call failed: {e}. Using regional fallback.")

        # If cache exists (even if stale), return it
        if cls._cache:
            return cls._cache

        # Otherwise return realistic regional fallback for Tambaram / Chennai semi-arid zone
        return cls._get_regional_fallback()

    @classmethod
    def _process_weather_payload(cls, raw: Dict[str, Any]) -> Dict[str, Any]:
        curr = raw.get("current", {})
        hourly = raw.get("hourly", {})
        daily = raw.get("daily", {})

        wmo_code = curr.get("weather_code", 0)
        desc, icon, category = WMO_CODE_MAP.get(wmo_code, ("Clear", "☀️", "Clear"))

        # Calculate upcoming 24-hour total precipitation and rain risk
        hourly_precip = hourly.get("precipitation", [])[:24]
        hourly_probs = hourly.get("precipitation_probability", [])[:24]
        hourly_et0 = hourly.get("et0_fao_evapotranspiration", [])[:24]

        total_rain_24h = round(sum(hourly_precip), 2)
        max_prob_24h = max(hourly_probs) if hourly_probs else 0
        avg_et0 = round(sum(hourly_et0) / len(hourly_et0), 2) if hourly_et0 else 4.2

        # Evaluate predictive rain suppression recommendation
        rain_suppression_active = total_rain_24h >= 5.0 or (max_prob_24h >= 75 and total_rain_24h >= 3.0)

        # 7-day daily forecast summary
        days_forecast = []
        daily_times = daily.get("time", [])
        daily_max_t = daily.get("temperature_2m_max", [])
        daily_min_t = daily.get("temperature_2m_min", [])
        daily_rain = daily.get("precipitation_sum", [])
        daily_prob = daily.get("precipitation_probability_max", [])
        daily_code = daily.get("weather_code", [])

        for i in range(len(daily_times)):
            d_code = daily_code[i] if i < len(daily_code) else 0
            d_desc, d_icon, _ = WMO_CODE_MAP.get(d_code, ("Clear", "☀️", "Clear"))
            days_forecast.append({
                "date": daily_times[i],
                "temp_max": round(daily_max_t[i], 1) if i < len(daily_max_t) else 33.0,
                "temp_min": round(daily_min_t[i], 1) if i < len(daily_min_t) else 24.0,
                "precipitation_mm": round(daily_rain[i], 1) if i < len(daily_rain) else 0.0,
                "precipitation_probability": daily_prob[i] if i < len(daily_prob) else 10,
                "condition": d_desc,
                "icon": d_icon
            })

        return {
            "source": "Open-Meteo Satellite & Meteorological Model",
            "location": LOCATION_NAME,
            "coordinates": {"latitude": ERUMAIYUR_LATITUDE, "longitude": ERUMAIYUR_LONGITUDE},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current": {
                "temperature": round(curr.get("temperature_2m", 32.5), 1),
                "apparent_temperature": round(curr.get("apparent_temperature", 35.0), 1),
                "humidity": round(curr.get("relative_humidity_2m", 68.0), 1),
                "relative_humidity": round(curr.get("relative_humidity_2m", 68.0), 1),
                "precipitation": round(curr.get("precipitation", 0.0), 1),
                "precipitation_mm": round(curr.get("precipitation", 0.0), 1),
                "wind_speed": round(curr.get("wind_speed_10m", 12.0), 1),
                "wind_speed_kmh": round(curr.get("wind_speed_10m", 12.0), 1),
                "wind_direction": int(curr.get("wind_direction_10m", 135)),
                "surface_pressure_hpa": round(curr.get("surface_pressure", 1012.0), 1),
                "weather_code": wmo_code,
                "condition": desc,
                "weather_description": desc,
                "icon": icon,
                "category": category,
                "reference_evapotranspiration_mm": avg_et0
            },
            "rain_suppression": {
                "suppress_irrigation": rain_suppression_active,
                "reason": (
                    f"⚠️ Rain Suppression Active: {total_rain_24h} mm rainfall forecast over Tambaram. "
                    "Irrigation pump suppressed to conserve water."
                    if rain_suppression_active
                    else "Clear skies forecasted. Regular precision irrigation schedule active."
                ),
                "expected_rain_6h_mm": round(sum(hourly_precip[:6]), 1) if len(hourly_precip) >= 6 else 0.0,
                "expected_rain_24h_mm": total_rain_24h
            },
            "forecast_24h": {
                "total_precipitation_mm": total_rain_24h,
                "max_rain_probability": max_prob_24h,
                "mean_et0_mm_day": avg_et0,
                "rain_suppression_recommended": rain_suppression_active,
                "alert_message": (
                    f"⚠️ Rain Suppression Active: {total_rain_24h} mm rainfall forecast over Tambaram. "
                    "Irrigation pump suppressed to conserve water."
                    if rain_suppression_active
                    else "No significant precipitation forecast. Standard ML predictive schedule active."
                )
            },
            "daily_7day": days_forecast,
            "hourly_next_12h": [
                {
                    "hour": i,
                    "temp": round(hourly.get("temperature_2m", [32.0]*24)[i], 1),
                    "humidity": round(hourly.get("relative_humidity_2m", [65.0]*24)[i], 1),
                    "rain_prob": hourly.get("precipitation_probability", [10]*24)[i],
                    "rain_mm": round(hourly.get("precipitation", [0.0]*24)[i], 1),
                }
                for i in range(min(12, len(hourly.get("temperature_2m", []))))
            ]
        }

    @classmethod
    def _get_regional_fallback(cls) -> Dict[str, Any]:
        """Provides realistic Tamil Nadu / Tambaram regional weather fallback."""
        return {
            "source": "Regional Agro-Climatic Baseline (Erumaiyur Fallback)",
            "location": LOCATION_NAME,
            "coordinates": {"latitude": ERUMAIYUR_LATITUDE, "longitude": ERUMAIYUR_LONGITUDE},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current": {
                "temperature": 32.4,
                "apparent_temperature": 35.2,
                "humidity": 68.0,
                "relative_humidity": 68.0,
                "precipitation": 0.0,
                "precipitation_mm": 0.0,
                "wind_speed": 14.2,
                "wind_speed_kmh": 14.2,
                "wind_direction": 135,
                "surface_pressure_hpa": 1012.0,
                "weather_code": 1,
                "condition": "Mainly clear",
                "weather_description": "Mainly clear",
                "icon": "🌤️",
                "category": "Clear",
                "reference_evapotranspiration_mm": 4.5
            },
            "rain_suppression": {
                "suppress_irrigation": False,
                "reason": "Clear conditions over Tambaram. Standard predictive scheduling active.",
                "expected_rain_6h_mm": 0.0,
                "expected_rain_24h_mm": 0.0
            },
            "forecast_24h": {
                "total_precipitation_mm": 0.0,
                "max_rain_probability": 15,
                "mean_et0_mm_day": 4.5,
                "rain_suppression_recommended": False,
                "alert_message": "Clear conditions over Tambaram. Standard predictive scheduling active."
            },
            "daily_7day": [
                {"date": "Today", "temp_max": 34.0, "temp_min": 25.0, "precipitation_mm": 0.0, "precipitation_probability": 15, "condition": "Mainly clear", "icon": "🌤️"},
                {"date": "Tomorrow", "temp_max": 33.5, "temp_min": 24.5, "precipitation_mm": 0.0, "precipitation_probability": 20, "condition": "Partly cloudy", "icon": "⛅"},
                {"date": "Day 3", "temp_max": 33.0, "temp_min": 24.0, "precipitation_mm": 1.2, "precipitation_probability": 35, "condition": "Light drizzle", "icon": "🌦️"},
                {"date": "Day 4", "temp_max": 32.0, "temp_min": 23.5, "precipitation_mm": 8.5, "precipitation_probability": 80, "condition": "Moderate rain", "icon": "🌧️"},
                {"date": "Day 5", "temp_max": 31.5, "temp_min": 23.0, "precipitation_mm": 3.0, "precipitation_probability": 55, "condition": "Scattered showers", "icon": "🌦️"},
                {"date": "Day 6", "temp_max": 33.0, "temp_min": 24.0, "precipitation_mm": 0.0, "precipitation_probability": 15, "condition": "Clear", "icon": "☀️"},
                {"date": "Day 7", "temp_max": 34.2, "temp_min": 25.1, "precipitation_mm": 0.0, "precipitation_probability": 10, "condition": "Clear", "icon": "☀️"}
            ],
            "hourly_next_12h": [
                {"hour": i, "temp": round(32.0 + (i * 0.2), 1), "humidity": 65, "rain_prob": 10, "rain_mm": 0.0}
                for i in range(12)
            ]
        }
