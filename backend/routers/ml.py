"""Machine Learning Router for IRRIGATEWISE.

Exposes endpoints for:
- 1h, 3h, 6h future soil moisture regression
- Multi-class crop recommendation classifier with probabilities
- Sensor anomaly screening
- Model registry and genuine performance metrics
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import get_db
import models
import schemas
# pyrefly: ignore [missing-import]
from ml.predict import SoilMoisturePredictor
# pyrefly: ignore [missing-import]
from ml.train_crop_model import CropRecommender
# pyrefly: ignore [missing-import]
from ml.anomaly_detection import check_sensor_anomaly
# pyrefly: ignore [missing-import]
from ml.model_registry import ModelRegistry

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

@router.post("/moisture/predict", response_model=schemas.MoisturePredictionOutput)
def predict_soil_moisture(
    payload: schemas.MoisturePredictionInput,
    db: Session = Depends(get_db)
):
    """Generates 1h, 3h, and 6h future soil moisture predictions and logs forecast."""
    predictor = SoilMoisturePredictor()
    result = predictor.predict(payload)
    
    # Store prediction into ml_predictions table for feedback tracking
    rec = models.MLPrediction(
        model_name=result.model_name,
        model_version=result.model_version,
        current_moisture=result.current_moisture,
        predicted_1h=result.predicted_1h,
        predicted_3h=result.predicted_3h,
        predicted_6h=result.predicted_6h,
        target_moisture=result.target_moisture,
        irrigation_required=1 if result.predicted_3h < 46.0 else 0,
        confidence_score=result.confidence_score,
        decision_mode="ml_predictive",
        timestamp=datetime.now(timezone.utc)
    )
    db.add(rec)
    db.commit()
    
    return result

@router.post("/crop/predict", response_model=schemas.CropPredictionOutput)
def predict_crop(payload: schemas.CropPredictionInput):
    """Predicts ranked crops with prediction probabilities based on N-P-K, pH, OC, and climate."""
    recommender = CropRecommender()
    res = recommender.predict(
        n=payload.nitrogen,
        p=payload.phosphorus,
        k=payload.potassium,
        ph=payload.ph,
        oc=payload.organic_carbon,
        temp=payload.temperature or 30.0,
        hum=payload.humidity or 70.0,
        rain=payload.rainfall or 100.0,
        soil_type=payload.soil_type or "loam"
    )
    return res

@router.post("/anomaly/check", response_model=schemas.AnomalyCheckOutput)
def check_anomaly(payload: schemas.AnomalyCheckInput):
    """Screens live telemetry for physical out-of-bounds, sudden spikes, or freezes."""
    res = check_sensor_anomaly(
        soil_moisture=payload.soil_moisture,
        temperature=payload.temperature,
        humidity=payload.humidity,
        pump_status=payload.pump_status or "OFF",
        previous_moisture=payload.previous_moisture
    )
    return res

@router.get("/models")
def get_registered_models(db: Session = Depends(get_db)):
    """Returns active production model info and registered versions."""
    active_info = ModelRegistry.get_active_model_details(db)
    db_versions = db.query(models.MLModelVersion).all()
    return {
        "active_production_model": active_info,
        "database_model_versions": [
            {
                "id": v.id,
                "model_name": v.model_name,
                "version_tag": v.version_tag,
                "mae": v.mae,
                "rmse": v.rmse,
                "r2_score": v.r2_score,
                "is_active": bool(v.is_active),
                "trained_at": v.trained_at.isoformat() if v.trained_at else None
            }
            for v in db_versions
        ]
    }

@router.get("/evaluation")
def get_model_evaluation_metrics():
    """Returns genuine evaluation metrics comparing Linear Regression, Random Forest, and Gradient Boosting."""
    return ModelRegistry.get_comparison_data()

@router.get("/metrics-comparison")
def get_full_metrics_comparison():
    """Returns visual-ready, multi-dimensional success metrics comparing ML models against Non-ML methods.

    Includes:
    - Multi-Horizon Regression metrics (1h, 3h, 6h) vs Naive and Statistical Baselines
    - 8x8 Crop Suitability Confusion Matrix Heatmap
    - 2x2 Sensor Anomaly Detection Confusion Matrix & ROC stats vs Static Bounds
    - Operational 30-Day Water Conservation & Root Stress Reduction Impact
    - 7-Day Diurnal Water Savings Heatmap Grid
    - Prediction Residual Error Distribution & Gaussian Bell Curve
    - 72-Hour Continuous Soil Moisture Simulation Trajectory
    """
    # pyrefly: ignore [missing-import]
    from ml.benchmark_service import BenchmarkService
    return BenchmarkService.get_full_benchmark_metrics()

@router.get("/evaluation-details")
def get_comprehensive_evaluation_details():
    """Returns authoritative model evaluation data including:
    - Comparison metrics across Linear Regression, Random Forest, Gradient Boosting
    - Genuine Actual vs Predicted test samples from held-out 15% test split (1,295 records)
    - Full residual distribution across 1h, 3h, 6h horizons
    - Feature importance from trained production model
    - Learning curve / training history availability status
    """
    comp = ModelRegistry.get_comparison_data()
    eval_pts = ModelRegistry.get_evaluation_points_data()
    # pyrefly: ignore [missing-import]
    from ml.benchmark_service import BenchmarkService
    full_benchmarks = BenchmarkService.get_full_benchmark_metrics()
    
    return {
        "model_comparison": comp,
        "evaluation_points": eval_pts,
        "baseline_comparison": full_benchmarks.get("models_comparison", []),
        "learning_curves": {
            "status": "unavailable",
            "reason": "Production model was fitted using scikit-learn HistGradientBoostingRegressor without epoch-by-epoch loss tracking (early_stopping=False). To preserve scientific integrity, synthetic loss curves are not fabricated.",
            "available_alternatives": "Validation and test partition summary metrics (MAE, RMSE, R²) are provided across all prediction horizons."
        }
    }

@router.get("/dl-evaluation")
def get_deep_learning_evaluation():
    """Returns authoritative Deep Learning Plant Pathology Model evaluation metrics.
    
    Includes:
    - MobileNetV3-Small architecture specs and parameter count (1.53M)
    - PlantVillage test accuracy (99.77%), precision, recall, and F1
    - 15-class precision/recall breakdown (including Septoria, Early Blight, Late Blight)
    - 15-epoch training loss and validation accuracy curves
    - Latency and edge-efficiency benchmark vs ResNet-50 and VGG-16
    """
    import os
    import json
    report_path = os.path.join(os.path.dirname(__file__), "..", "ml", "artifacts", "plant_disease_model", "dl_evaluation_report.json")
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            return json.load(f)
    from ml.evaluate_dl_model import generate_dl_evaluation_report
    return generate_dl_evaluation_report()


