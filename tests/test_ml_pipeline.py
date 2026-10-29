import os
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore
import pandas as pd
# pyrefly: ignore [missing-import]
from ml.feature_engineering import (
    engineer_timeseries_features,
    build_single_inference_vector,
    FEATURE_COLUMNS,
    TARGET_COLUMNS
)
# pyrefly: ignore [missing-import]
from ml.predict import SoilMoisturePredictor
# pyrefly: ignore [missing-import]
from schemas import MoisturePredictionInput

def test_feature_engineering_dimensions():
    """Verifies temporal feature extraction produces all expected features without NaNs."""
    df_raw = pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=20, freq="h"),
        "soil_moisture": [50.0 + i * 0.5 for i in range(20)],
        "temperature": [30.0 + (i % 5) for i in range(20)],
        "humidity": [70.0 - (i % 5) for i in range(20)],
        "rainfall": [0.0] * 20,
        "wind_speed": [12.0] * 20,
        "soil_type": ["loam"] * 20,
        "crop_type": ["Samba Rice"] * 20,
        "irrigation_amount": [0.0] * 20,
        "irrigation_duration": [0.0] * 20,
        "pump_status": ["OFF"] * 20,
        "hydrogel_present": [1] * 20,
        "hydrogel_dosage": [50.0] * 20,
        "hours_since_irrigation": [float(i) for i in range(20)],
        "future_soil_moisture_1h": [51.0] * 20,
        "future_soil_moisture_3h": [52.0] * 20,
        "future_soil_moisture_6h": [53.0] * 20,
    })
    
    df_feat = engineer_timeseries_features(df_raw)
    for col in FEATURE_COLUMNS:
        assert col in df_feat.columns, f"Missing feature column: {col}"
    assert not bool(df_feat[FEATURE_COLUMNS].isna().to_numpy().any()), "Features contain unexpected NaNs"

def test_single_inference_vector_shape():
    """Verifies online real-time inference vector has correct dimensionality."""
    vec = build_single_inference_vector(
        current_moisture=45.0,
        temperature=32.0,
        humidity=65.0,
        rainfall=0.0,
        wind_speed=12.0,
        soil_type="loam",
        hydrogel_present=1,
        hydrogel_dosage=50.0,
        hours_since_irrigation=10.0,
        hour_of_day=14
    )
    assert vec.shape == (1, len(FEATURE_COLUMNS)), f"Shape mismatch: {vec.shape} vs {(1, len(FEATURE_COLUMNS))}"

def test_moisture_prediction_inference():
    """Verifies trained model produces valid bounded predictions across horizons."""
    predictor = SoilMoisturePredictor()
    input_data = MoisturePredictionInput(
        current_moisture=42.0,
        temperature=33.0,
        humidity=62.0,
        rainfall=0.0,
        wind_speed=14.0,
        soil_type="loam",
        crop_type="Samba Rice",
        hydrogel_present=1,
        target_moisture=65.0
    )
    output = predictor.predict(input_data)
    assert 5.0 <= output.predicted_1h <= 95.0
    assert 5.0 <= output.predicted_3h <= 95.0
    assert 5.0 <= output.predicted_6h <= 95.0
    assert output.model_name in ["Gradient Boosting", "Random Forest", "Linear Regression"]
    assert output.confidence_score is not None
    assert output.feature_importance is not None
    assert len(output.feature_importance) > 0

def test_terrace_crop_recommendation_classifier():
    """Verifies retrained multi-class ML crop recommender predicts terrace container plants."""
    # pyrefly: ignore [missing-import]
    from ml.train_crop_model import CropRecommender
    recommender = CropRecommender()
    
    # 1. Potted tomato conditions
    res_tomato = recommender.predict(
        n=115.0, p=55.0, k=220.0, ph=6.4, oc=1.1,
        temp=28.0, hum=70.0, rain=100.0, soil_type="loam"
    )
    assert res_tomato["recommended_crop"] in ["Bush Tomato", "Cherry Tomato"]
    assert res_tomato["confidence"] >= 0.50
    assert len(res_tomato["top_candidates"]) == 4
    
    # 2. Leafy greens / spinach conditions
    res_spinach = recommender.predict(
        n=95.0, p=35.0, k=110.0, ph=6.6, oc=1.15,
        temp=25.0, hum=75.0, rain=60.0, soil_type="loam"
    )
    assert res_spinach["recommended_crop"] in ["Indian Spinach", "Amaranth Keerai"]
    assert res_spinach["confidence"] >= 0.50
    assert len(res_spinach["top_candidates"]) == 4

