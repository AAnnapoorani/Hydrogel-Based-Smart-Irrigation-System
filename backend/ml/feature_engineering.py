"""Feature Engineering Pipeline for IRRIGATEWISE Soil Moisture Forecasting.

Transforms raw temporal sensor streams into rich, non-leaking feature vectors
for multi-horizon soil moisture regression.
"""

import math
from datetime import datetime
# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any, Optional

FEATURE_COLUMNS = [
    "soil_moisture",
    "temperature",
    "humidity",
    "rainfall",
    "wind_speed",
    "hydrogel_present",
    "hydrogel_dosage",
    "hours_since_irrigation",
    "hour_sin",
    "hour_cos",
    "moisture_lag_1",
    "moisture_lag_2",
    "moisture_lag_3",
    "moisture_rolling_mean_3",
    "moisture_rolling_mean_6",
    "moisture_rolling_std_6",
    "moisture_rate_of_change",
    "temp_lag_1",
    "humidity_lag_1",
    "evap_stress_index",
    "soil_clay",
    "soil_loam",
    "soil_sandy",
]

TARGET_COLUMNS = [
    "future_soil_moisture_1h",
    "future_soil_moisture_3h",
    "future_soil_moisture_6h",
]

def engineer_timeseries_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts temporal, rolling, lag, and physical interaction features.

    Maintains temporal causality to prevent forward data leakage.
    """
    df = df.copy()
    
    # Parse timestamp if string
    if "timestamp" in df.columns:
        df["dt"] = pd.to_datetime(df["timestamp"])
        df["hour"] = df["dt"].dt.hour
    else:
        df["hour"] = 12  # default midday if absent
        
    # 1. Cyclical Diurnal Time Encoding
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
    
    # 2. Moisture Lag Features (Past measurements only)
    df["moisture_lag_1"] = df["soil_moisture"].shift(1)
    df["moisture_lag_2"] = df["soil_moisture"].shift(2)
    df["moisture_lag_3"] = df["soil_moisture"].shift(3)
    
    # 3. Environmental Lags
    df["temp_lag_1"] = df["temperature"].shift(1)
    df["humidity_lag_1"] = df["humidity"].shift(1)
    
    # 4. Rolling Window Aggregations (Closed on left to avoid leakage)
    df["moisture_rolling_mean_3"] = df["soil_moisture"].rolling(window=3, closed="left").mean()
    df["moisture_rolling_mean_6"] = df["soil_moisture"].rolling(window=6, closed="left").mean()
    df["moisture_rolling_std_6"] = df["soil_moisture"].rolling(window=6, closed="left").std().fillna(0.0)
    
    # 5. Differential Features
    df["moisture_rate_of_change"] = df["soil_moisture"] - df["moisture_lag_1"]
    
    # 6. Evaporative Stress Interaction (Vapor Pressure Deficit proxy)
    df["evap_stress_index"] = (df["temperature"] / 40.0) * (1.0 - df["humidity"] / 100.0) * (1.0 + df["wind_speed"] / 20.0)
    
    # 7. Soil Texture One-Hot Encoding
    soil_type = df["soil_type"].str.lower() if "soil_type" in df.columns else pd.Series(["loam"] * len(df))
    df["soil_clay"] = (soil_type == "clay").astype(int)
    df["soil_loam"] = (soil_type.isin(["loam", "cocopeat_mix", "potting_mix"])).astype(int)
    df["soil_sandy"] = (soil_type == "sandy").astype(int)
    
    # Fill initial lag NaNs with backward fill or base values
    df["moisture_lag_1"] = df["moisture_lag_1"].fillna(df["soil_moisture"])
    df["moisture_lag_2"] = df["moisture_lag_2"].fillna(df["moisture_lag_1"])
    df["moisture_lag_3"] = df["moisture_lag_3"].fillna(df["moisture_lag_2"])
    df["temp_lag_1"] = df["temp_lag_1"].fillna(df["temperature"])
    df["humidity_lag_1"] = df["humidity_lag_1"].fillna(df["humidity"])
    df["moisture_rolling_mean_3"] = df["moisture_rolling_mean_3"].fillna(df["soil_moisture"])
    df["moisture_rolling_mean_6"] = df["moisture_rolling_mean_6"].fillna(df["soil_moisture"])
    df["moisture_rate_of_change"] = df["moisture_rate_of_change"].fillna(0.0)
    
    return df

def build_single_inference_vector(
    current_moisture: float,
    temperature: float,
    humidity: float,
    rainfall: float = 0.0,
    wind_speed: float = 10.0,
    soil_type: str = "loam",
    hydrogel_present: int = 1,
    hydrogel_dosage: float = 50.0,
    hours_since_irrigation: float = 12.0,
    hour_of_day: Optional[int] = None,
    previous_moisture_1: Optional[float] = None,
    previous_moisture_2: Optional[float] = None,
    previous_moisture_3: Optional[float] = None,
) -> np.ndarray:
    """Constructs a single feature vector for online real-time inference."""
    if hour_of_day is None:
        hour_of_day = datetime.now().hour
        
    hour_sin = math.sin(2 * math.pi * hour_of_day / 24.0)
    hour_cos = math.cos(2 * math.pi * hour_of_day / 24.0)
    
    lag_1 = previous_moisture_1 if previous_moisture_1 is not None else current_moisture
    lag_2 = previous_moisture_2 if previous_moisture_2 is not None else lag_1
    lag_3 = previous_moisture_3 if previous_moisture_3 is not None else lag_2
    
    roll_mean_3 = (current_moisture + lag_1 + lag_2) / 3.0
    roll_mean_6 = (current_moisture + lag_1 + lag_2 + lag_3) / 4.0
    roll_std_6 = float(np.std([current_moisture, lag_1, lag_2, lag_3]))
    rate_of_change = current_moisture - lag_1
    
    evap_stress = (temperature / 40.0) * (1.0 - humidity / 100.0) * (1.0 + wind_speed / 20.0)
    
    st = soil_type.lower()
    is_clay = 1 if st == "clay" else 0
    is_loam = 1 if st in ["loam", "cocopeat_mix", "potting_mix"] else 0
    is_sandy = 1 if st == "sandy" else 0
    
    vec = [
        current_moisture,
        temperature,
        humidity,
        rainfall,
        wind_speed,
        hydrogel_present,
        hydrogel_dosage if hydrogel_present else 0.0,
        hours_since_irrigation,
        hour_sin,
        hour_cos,
        lag_1,
        lag_2,
        lag_3,
        roll_mean_3,
        roll_mean_6,
        roll_std_6,
        rate_of_change,
        temperature,  # temp_lag_1 proxy
        humidity,     # hum_lag_1 proxy
        evap_stress,
        is_clay,
        is_loam,
        is_sandy,
    ]
    return np.array(vec, dtype=np.float32).reshape(1, -1)
