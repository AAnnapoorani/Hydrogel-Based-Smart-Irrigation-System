"""Physics-Informed Dataset Generator for IRRIGATEWISE.

=============================================================================
DATASET CLASSIFICATION: DEVELOPMENT / SIMULATION DATASET
PHYSICS ENGINE: Hydrogel Sorption-Desorption & Soil Water Potential Dynamics
RANDOM SEED: 42 (Fully Reproducible)
=============================================================================

This script generates synthetic, physics-grounded time-series data for
training soil moisture forecasting models and comparing moisture retention
dynamics between:
1. CONTROL SOIL (without hydrogel)
2. HYDROGEL-AMENDED SOIL (with hydrogel polymer dosage)

The simulation enforces:
- Diurnal solar thermal cycles
- Evapotranspiration driven by temperature, humidity, wind, and crop coefficients
- Soil texture retention limits (clay, loam, sandy)
- Hydrogel osmotic buffer release kinetics
- Actuator events (irrigation pump pulses) and rainfall events
- Continuous temporal continuity without synthetic random jumps
"""

import os
import math
import random
# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Optional

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

def calculate_et0(temperature: float, humidity: float, wind_speed: float) -> float:
    """Simplified Penman-Monteith / Hargreaves daily evapotranspiration rate (mm/h)."""
    # Vapor pressure deficit factor
    es = 0.6108 * math.exp((17.27 * temperature) / (temperature + 237.3))
    ea = es * (humidity / 100.0)
    vpd = max(0.1, es - ea)
    
    # ET proxy
    et0 = (0.0135 * (temperature + 17.8) * vpd + 0.05 * (wind_speed / 10.0))
    return max(0.05, et0)

def generate_sensor_timeseries(
    days: int = 45,
    interval_hours: int = 1,
    start_date: datetime = datetime(2026, 8, 15, 0, 0, tzinfo=timezone.utc),
    soil_type: str = "cocopeat_mix",
    crop_type: str = "Terrace Container Garden",
    hydrogel_present: int = 1,
    hydrogel_dosage: float = 25.0  # 25g per container pot
) -> pd.DataFrame:
    """Generates continuous time-series sensor data for a specific field condition."""
    total_hours = days * 24
    
    # Soil texture specific constants
    texture_params = {
        "sandy": {"fc": 20.0, "pwp": 8.0,  "drain_rate": 0.45, "et_mult": 1.25},
        "loam":  {"fc": 34.0, "pwp": 14.0, "drain_rate": 0.22, "et_mult": 1.00},
        "clay":  {"fc": 44.0, "pwp": 22.0, "drain_rate": 0.12, "et_mult": 0.85},
        "cocopeat_mix": {"fc": 42.0, "pwp": 16.0, "drain_rate": 0.20, "et_mult": 0.95},
    }
    params = texture_params.get(soil_type, texture_params["loam"])
    
    fc = params["fc"]          # Field capacity (%)
    drain_rate = params["drain_rate"]
    et_mult = params["et_mult"]
    
    # Hydrogel buffering coefficient
    # Hydrogel reduces gravitational drainage and buffers evapotranspiration
    if hydrogel_present:
        drain_damping = 1.0 / (1.0 + 0.03 * hydrogel_dosage)
        et_retention = 1.0 / (1.0 + 0.015 * hydrogel_dosage)
    else:
        drain_damping = 1.0
        et_retention = 1.0

    records = []
    
    # Initial state
    current_moisture = 60.0
    hours_since_irrigation = 48.0
    pump_status = "OFF"
    
    current_time = start_date
    
    for h in range(total_hours):
        hour_of_day = current_time.hour
        day_of_year = current_time.timetuple().tm_yday
        
        # Diurnal temperature cycle: peaks around 14:00, lowest at 05:00
        solar_elevation = math.sin(math.pi * (hour_of_day - 5) / 14) if 5 <= hour_of_day <= 19 else 0.0
        base_temp = 28.0 + 2.0 * math.sin(2 * math.pi * day_of_year / 365.0)
        diurnal_temp = 7.0 * math.sin(2 * math.pi * (hour_of_day - 9) / 24.0)
        temp_noise = np.random.normal(0, 0.4)
        temperature = round(base_temp + diurnal_temp + temp_noise, 1)
        
        # Humidity inversely tracks temperature
        base_hum = 75.0 - 20.0 * (solar_elevation)
        hum_noise = np.random.normal(0, 1.5)
        humidity = round(max(30.0, min(95.0, base_hum + hum_noise)), 1)
        
        # Wind speed (higher in afternoon)
        wind_speed = round(max(2.0, 10.0 + 6.0 * solar_elevation + np.random.normal(0, 1.8)), 1)
        
        # Stochastic episodic rainfall events (monsoon pulses)
        is_raining = random.random() < 0.02
        rainfall = round(random.uniform(4.0, 25.0), 1) if is_raining else 0.0
        
        # Irrigation actuation check
        # Under rule-based simulation, irrigate when moisture drops below threshold (e.g. 42%)
        irrigation_amount = 0.0
        irrigation_duration = 0.0
        
        if current_moisture < 42.0 and not is_raining and hours_since_irrigation >= 12.0:
            pump_status = "ON"
            irrigation_duration = 15.0  # minutes
            irrigation_amount = 12.0    # L/m²
            hours_since_irrigation = 0.0
        else:
            pump_status = "OFF"
            hours_since_irrigation += 1.0

        # Physical moisture updates
        # 1. Moisture influx
        if rainfall > 0.0:
            # Hydrogel absorbs and stores more rainfall into soil matrix
            absorption_factor = 0.85 if hydrogel_present else 0.60
            current_moisture += rainfall * absorption_factor
            hours_since_irrigation = max(hours_since_irrigation, 24.0)
            
        if irrigation_amount > 0.0:
            current_moisture += irrigation_amount * 1.5
            
        # 2. Moisture efflux (Evapotranspiration & Drainage)
        et0 = calculate_et0(temperature, humidity, wind_speed)
        hourly_loss = et0 * et_mult * et_retention * 0.45
        
        # Gravity drainage if above field capacity
        if current_moisture > fc:
            excess = current_moisture - fc
            drainage_loss = excess * drain_rate * drain_damping
            current_moisture -= drainage_loss
            
        current_moisture -= hourly_loss
        
        # Add slight natural sensor measurement variation
        sensor_reading = round(max(10.0, min(92.0, current_moisture + np.random.normal(0, 0.2))), 2)
        
        records.append({
            "timestamp": current_time.isoformat(),
            "soil_moisture": sensor_reading,
            "temperature": temperature,
            "humidity": humidity,
            "rainfall": rainfall,
            "wind_speed": wind_speed,
            "soil_type": soil_type,
            "crop_type": crop_type,
            "irrigation_amount": irrigation_amount,
            "irrigation_duration": irrigation_duration,
            "pump_status": pump_status,
            "hydrogel_present": hydrogel_present,
            "hydrogel_dosage": hydrogel_dosage if hydrogel_present else 0.0,
            "hours_since_irrigation": round(hours_since_irrigation, 1),
        })
        
        current_time += timedelta(hours=interval_hours)
        
    df = pd.DataFrame(records)
    
    # Compute supervised future targets (1h, 3h, 6h forward shift)
    df["future_soil_moisture_1h"] = df["soil_moisture"].shift(-1)
    df["future_soil_moisture_3h"] = df["soil_moisture"].shift(-3)
    df["future_soil_moisture_6h"] = df["soil_moisture"].shift(-6)
    
    # Drop rows at the end where target shifts become NaN
    df = df.dropna().reset_index(drop=True)
    return df

def generate_complete_dataset(output_path: Optional[str] = None):
    """Generates combined dataset with both Hydrogel-treated and Control plots."""
    if output_path is None:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        output_path = os.path.join(root_dir, "datasets", "moisture_iot", "sensor_timeseries_dataset.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"Generating 45-day terrace garden dataset starting 15 August 2026 (Seed: {SEED})...")
    
    # Plot A: With Hydrogel (25g per container pot)
    df_hydrogel = generate_sensor_timeseries(
        days=45,
        interval_hours=1,
        start_date=datetime(2026, 8, 15, 0, 0, tzinfo=timezone.utc),
        soil_type="cocopeat_mix",
        crop_type="Terrace Container Garden",
        hydrogel_present=1,
        hydrogel_dosage=25.0
    )
    
    # Plot B: Without Hydrogel (Control 0g)
    df_control = generate_sensor_timeseries(
        days=45,
        interval_hours=1,
        start_date=datetime(2026, 8, 15, 0, 0, tzinfo=timezone.utc),
        soil_type="cocopeat_mix",
        crop_type="Terrace Container Garden",
        hydrogel_present=0,
        hydrogel_dosage=0.0
    )
    
    combined_df = pd.concat([df_hydrogel, df_control], ignore_index=True)
    
    # Write metadata comments at the top
    metadata_header = (
        "# IRRIGATEWISE RESEARCH DATASET\n"
        "# CLASSIFICATION: DEVELOPMENT / SIMULATION DATASET (Physics-Informed)\n"
        "# PURPOSE: 45-Day Terrace Garden Soil Moisture Forecasting & Hydrogel Retention Analysis (15 Aug 2026 - 28 Sep 2026)\n"
        "# LOCATION: Erumaiyur Village, Tambaram, Tamil Nadu\n"
        f"# GENERATION DATE: {datetime.now(timezone.utc).isoformat()}\n"
        f"# TOTAL RECORDS: {len(combined_df)}\n"
        "# COLUMNS: timestamp, soil_moisture, temperature, humidity, rainfall, wind_speed, soil_type, crop_type, irrigation_amount, irrigation_duration, pump_status, hydrogel_present, hydrogel_dosage, hours_since_irrigation, future_soil_moisture_1h, future_soil_moisture_3h, future_soil_moisture_6h\n"
    )
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(metadata_header)
        combined_df.to_csv(f, index=False)
        
    print(f"Dataset successfully created at: {output_path}")
    print(f"Total records generated: {len(combined_df)} (Hydrogel: {len(df_hydrogel)}, Control: {len(df_control)})")
    
    # Compute and display retention summary
    avg_moist_h = df_hydrogel['soil_moisture'].mean()
    avg_moist_c = df_control['soil_moisture'].mean()
    irrigations_h = (df_hydrogel['pump_status'] == 'ON').sum()
    irrigations_c = (df_control['pump_status'] == 'ON').sum()
    
    print(f"--- SIMULATION HYDROGEL RETENTION BENCHMARK ---")
    print(f"Control Plot (No Hydrogel)    : Avg Moisture = {avg_moist_c:.1f}%, Irrigation Events = {irrigations_c}")
    print(f"Treatment Plot (With Hydrogel): Avg Moisture = {avg_moist_h:.1f}%, Irrigation Events = {irrigations_h}")
    if irrigations_c > 0:
        water_saving_events = ((irrigations_c - irrigations_h) / irrigations_c) * 100
        print(f"Irrigation Event Reduction: {water_saving_events:.1f}%")
        
    return output_path

if __name__ == "__main__":
    generate_complete_dataset()
