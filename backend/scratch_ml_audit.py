"""Comprehensive ML & Deep Learning Effectiveness Audit Script for IRRIGATEWISE.

Evaluates all 5 core AI/ML/DL models:
1. Multi-Horizon Soil Moisture Regression (Gradient Boosting / HistGradientBoosting)
2. Sensor Anomaly Detection (Isolation Forest)
3. Terrace Crop Classification (Random Forest 14-Class)
4. Computer Vision Foliar Disease & Pest Diagnostics (PlantHealthService)
5. Physics-Informed Hydration & Hydrogel Kinetics Decision Engine
"""

import time
import json
import numpy as np
from PIL import Image

# 1. Soil Moisture Predictor
print("=" * 70)
print("1. EVALUATING MULTI-HORIZON SOIL MOISTURE REGRESSION MODEL")
print("=" * 70)
from ml.predict import SoilMoisturePredictor
from schemas import MoisturePredictionInput

t0 = time.perf_counter()
predictor = SoilMoisturePredictor()
load_time = (time.perf_counter() - t0) * 1000

test_input = MoisturePredictionInput(
    current_moisture=42.5,
    temperature=32.0,
    humidity=65.0,
    rainfall=0.0,
    wind_speed=12.0,
    soil_type="loam",
    crop_type="Bush Tomato",
    hydrogel_present=1,
    hydrogel_dosage=25.0,
    target_moisture=60.0
)

t0 = time.perf_counter()
pred_output = predictor.predict(test_input)
inf_time = (time.perf_counter() - t0) * 1000

print(f"Model Name: {pred_output.model_name}")
print(f"Model Version: {pred_output.model_version}")
print(f"Cold Start / Load Time: {load_time:.2f} ms")
print(f"Single Inference Latency: {inf_time:.2f} ms")
conf_pct = f"{pred_output.confidence_score * 100:.1f}%" if pred_output.confidence_score is not None else "N/A"
print(f"Confidence Score: {conf_pct}")
print(f"Predictions: +1h={pred_output.predicted_1h:.1f}%, +3h={pred_output.predicted_3h:.1f}%, +6h={pred_output.predicted_6h:.1f}%")
print(f"Top 3 Feature Importances:")
feat_items = (pred_output.feature_importance or {}).items()
top_feats = sorted(feat_items, key=lambda x: x[1], reverse=True)[:3]
for feat, imp in top_feats:
    print(f"   • {feat}: {imp:.4f}")

# 2. Sensor Anomaly Detection
print("\n" + "=" * 70)
print("2. EVALUATING SENSOR ANOMALY DETECTION (ISOLATION FOREST + 5-TIER GUARDRAILS)")
print("=" * 70)
from ml.anomaly_detection import AnomalyDetector

detector = AnomalyDetector()

# Normal reading
t0 = time.perf_counter()
normal_res = detector.check_telemetry(soil_moisture=55.0, temperature=30.0, humidity=68.0)
ano_inf_time = (time.perf_counter() - t0) * 1000

# Anomaly reading 1: Out of bounds negative moisture
oob_res = detector.check_telemetry(soil_moisture=-5.0, temperature=30.0, humidity=68.0)
# Anomaly reading 2: Sudden impossible spike (ADC short / fast jump without pump)
spike_res = detector.check_telemetry(soil_moisture=98.0, temperature=30.0, humidity=68.0, previous_moisture=40.0, pump_status="OFF")
# Anomaly reading 3: Sensor freeze
freeze_res = detector.check_telemetry(soil_moisture=45.0, temperature=30.0, humidity=68.0, recent_history=[45.0, 45.0, 45.0, 45.0, 45.0, 45.0])
# Anomaly reading 4: Actuator decoupling (Pump ON, zero moisture delta)
pump_fail_res = detector.check_telemetry(soil_moisture=35.0, temperature=30.0, humidity=68.0, previous_moisture=35.0, pump_status="ON")

print(f"Anomaly Detection Latency: {ano_inf_time:.2f} ms")
print(f"Normal Sample (55% SM, 30°C): IsAnomaly={normal_res['is_anomaly']}, Status={normal_res['status']}")
print(f"Tier 1 Physical Limit (-5% SM): IsAnomaly={oob_res['is_anomaly']}, Type={oob_res['anomaly_type']}, Severity={oob_res['severity']}")
print(f"Tier 2 Sudden Spike (40%->98% SM): IsAnomaly={spike_res['is_anomaly']}, Type={spike_res['anomaly_type']}, Severity={spike_res['severity']}")
print(f"Tier 3 Sensor Freeze (Flatline): IsAnomaly={freeze_res['is_anomaly']}, Type={freeze_res['anomaly_type']}, Severity={freeze_res['severity']}")
print(f"Tier 4 Pump Decoupling (Pump ON, SM Flat): IsAnomaly={pump_fail_res['is_anomaly']}, Type={pump_fail_res['anomaly_type']}, Severity={pump_fail_res['severity']}")

# 3. Terrace Crop Classification
print("\n" + "=" * 70)
print("3. EVALUATING TERRACE CROP CLASSIFICATION (RANDOM FOREST 14-CLASS)")
print("=" * 70)
from ml.train_crop_model import CropRecommender

recommender = CropRecommender()

t0 = time.perf_counter()
crop_res = recommender.predict(
    n=115.0, p=55.0, k=220.0, ph=6.4, oc=1.1,
    temp=28.0, hum=70.0, rain=100.0, soil_type="loam"
)
crop_inf_time = (time.perf_counter() - t0) * 1000

print(f"Classifier Latency: {crop_inf_time:.2f} ms")
print(f"Input: High N-P-K Tomato Mix (N=115, P=55, K=220, pH=6.4)")
print(f"Recommended Crop: {crop_res['recommended_crop']} (Confidence: {crop_res['confidence']*100:.1f}%)")
print("Top 3 Candidates:")
for c in crop_res['top_candidates'][:3]:
    print(f"   • {c['crop']}: {c['probability']*100:.1f}%")

# Test spinach/herb mix
crop_res2 = recommender.predict(
    n=95.0, p=35.0, k=110.0, ph=6.6, oc=1.15,
    temp=25.0, hum=75.0, rain=60.0, soil_type="loam"
)
print(f"\nInput: Herb/Greens Mix (N=95, P=35, K=110, pH=6.6)")
print(f"Recommended Crop: {crop_res2['recommended_crop']} (Confidence: {crop_res2['confidence']*100:.1f}%)")

# 4. Computer Vision Foliar Disease & Pest Diagnostics
print("\n" + "=" * 70)
print("4. EVALUATING COMPUTER VISION FOLIAR DISEASE & PEST SCREENING")
print("=" * 70)
from services.plant_health_service import PlantHealthService

# Create synthetic leaf test images:
# A: Healthy Green Leaf Image
img_healthy = Image.new("RGB", (256, 256), color=(45, 140, 50))
# B: Diseased Leaf Image with Necrotic Spots and Chlorosis
img_diseased = Image.new("RGB", (256, 256), color=(180, 160, 40))
for x in range(60, 120):
    for y in range(60, 120):
        img_diseased.putpixel((x, y), (90, 45, 20))

t0 = time.perf_counter()
diag_healthy = PlantHealthService.analyze_plant_disease(img_healthy, plant_hint="Tomato")
cv_time = (time.perf_counter() - t0) * 1000

diag_diseased = PlantHealthService.analyze_plant_disease(img_diseased, plant_hint="Tomato", symptom_hint="brown concentric spots")

print(f"CV Feature Extraction & Inference Latency: {cv_time:.2f} ms")
print(f"Healthy Leaf Sample: Diagnosis='{diag_healthy.primary_condition}', Conf={diag_healthy.confidence:.1f}%, Status={diag_healthy.status}")
print(f"Symptomatic Leaf Sample: Diagnosis='{diag_diseased.primary_condition}', Conf={diag_diseased.confidence:.1f}%, Status={diag_diseased.status}")
print(f"Organic Remediation Protocol: {diag_diseased.organic_remediation[0] if diag_diseased.organic_remediation else 'None'}")

# 5. Physics-Informed Hydration & Hydrogel Kinetics Decision Engine
print("\n" + "=" * 70)
print("5. EVALUATING HYBRID PHYSICS-AI IRRIGATION DECISION ENGINE")
print("=" * 70)
from services.irrigation_decision_engine import IrrigationDecisionEngine
from schemas import PredictiveDecisionInput

dec_input = PredictiveDecisionInput(
    current_moisture=38.0,
    target_moisture=60.0,
    temperature=33.0,
    humidity=60.0,
    wind_speed=12.0,
    rainfall_forecast_6h=0.0,
    soil_texture="cocopeat_mix",
    crop_type="Potted Tomato",
    hydrogel_present=1,
    pot_count=10,
    container_volume_litres=15.0,
    hours_since_irrigation=18.0
)

t0 = time.perf_counter()
decision = IrrigationDecisionEngine.evaluate(dec_input)
dec_time = (time.perf_counter() - t0) * 1000

print(f"Decision Engine Latency: {dec_time:.2f} ms")
print(f"Irrigation Required: {decision.irrigation_required}")
print(f"Water Required: {decision.water_required_ml:.1f} mL total ({decision.water_per_pot_ml:.1f} mL/pot across {decision.pot_count} pots)")
print(f"Estimated Pump Runtime: {decision.estimated_pump_duration_minutes * 60:.1f} seconds")
print(f"Decision Mode: {decision.decision_mode}")
print(f"Hydrogel Buffering Active: {decision.hydrogel_buffering_active}")
print(f"Water Saving Advantage: {decision.comparison.water_saving_advantage_pct:.1f}% vs traditional flood/rule irrigation")
print(f"Rule-Based vs ML Comparison: Rule={decision.comparison.rule_based_water_ml:.1f} mL | ML={decision.comparison.ml_predictive_water_ml:.1f} mL")
print(f"Reasoning: {decision.reason}")
print("=" * 70)
