"""Soil Moisture Forecasting Training Pipeline.

Trains and rigorously compares multiple regression algorithms:
1. Linear Regression (Baseline)
2. Random Forest Regressor
3. Gradient Boosting Regressor (HistGradientBoostingRegressor)

Targets:
- future_soil_moisture_1h
- future_soil_moisture_3h
- future_soil_moisture_6h

Evaluation Protocol:
- Chronological temporal train/val/test splitting (70% / 15% / 15%)
- Strict prohibition of random shuffling to prevent temporal data leakage
- Evaluated on test set using MAE, RMSE, and R²
- Model artifacts and comparison metrics serialized to backend/ml/artifacts/
"""

import os
import json
# pyrefly: ignore [missing-import]
import joblib
from typing import Tuple, Dict, Any, Optional, cast
# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ml.feature_engineering import (
    engineer_timeseries_features,
    FEATURE_COLUMNS,
    TARGET_COLUMNS
)

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def load_and_preprocess_dataset(csv_path: Optional[str] = None) -> pd.DataFrame:
    """Loads sensor dataset and extracts engineered temporal features."""
    if csv_path is None:
        # Search canonical datasets directory first, then fallback
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        canonical_path = os.path.join(root_dir, "datasets", "moisture_iot", "sensor_timeseries_dataset.csv")
        legacy_path = os.path.join(root_dir, "data", "generated", "sensor_timeseries_dataset.csv")
        
        if os.path.exists(canonical_path):
            csv_path = canonical_path
        elif os.path.exists(legacy_path):
            csv_path = legacy_path
        else:
            csv_path = canonical_path
        
    if not os.path.exists(csv_path):
        from ml.generate_dataset import generate_complete_dataset
        csv_path = generate_complete_dataset(csv_path)
        
    df = pd.read_csv(csv_path, comment="#")
    df_feat = engineer_timeseries_features(df)
    
    # Ensure no NaN values remain
    df_clean = df_feat.dropna(subset=FEATURE_COLUMNS + TARGET_COLUMNS).reset_index(drop=True)
    return df_clean

def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15
) -> Tuple:
    """Chronologically splits time-series data to avoid forward-looking data leakage."""
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    
    train_df = df.iloc[:train_end]
    val_df = df.iloc[train_end:val_end]
    test_df = df.iloc[val_end:]
    
    X_train = train_df[FEATURE_COLUMNS].values
    y_train = train_df[TARGET_COLUMNS].values
    
    X_val = val_df[FEATURE_COLUMNS].values
    y_val = val_df[TARGET_COLUMNS].values
    
    X_test = test_df[FEATURE_COLUMNS].values
    y_test = test_df[TARGET_COLUMNS].values
    
    return X_train, y_train, X_val, y_val, X_test, y_test

def evaluate_predictions(y_true: Any, y_pred: Any) -> Dict[str, Any]:
    """Computes MAE, RMSE, and R² across multi-target forecasting horizons."""
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred)
    mae_overall = float(mean_absolute_error(cast(Any, y_true_arr), cast(Any, y_pred_arr)))
    rmse_overall = float(np.sqrt(mean_squared_error(cast(Any, y_true_arr), cast(Any, y_pred_arr))))
    r2_overall = float(r2_score(cast(Any, y_true_arr), cast(Any, y_pred_arr)))
    
    # Per horizon metrics
    mae_1h = float(mean_absolute_error(cast(Any, y_true_arr[:, 0]), cast(Any, y_pred_arr[:, 0])))
    rmse_1h = float(np.sqrt(mean_squared_error(cast(Any, y_true_arr[:, 0]), cast(Any, y_pred_arr[:, 0]))))
    r2_1h = float(r2_score(cast(Any, y_true_arr[:, 0]), cast(Any, y_pred_arr[:, 0])))
    
    mae_3h = float(mean_absolute_error(cast(Any, y_true_arr[:, 1]), cast(Any, y_pred_arr[:, 1])))
    rmse_3h = float(np.sqrt(mean_squared_error(cast(Any, y_true_arr[:, 1]), cast(Any, y_pred_arr[:, 1]))))
    r2_3h = float(r2_score(cast(Any, y_true_arr[:, 1]), cast(Any, y_pred_arr[:, 1])))
    
    mae_6h = float(mean_absolute_error(cast(Any, y_true_arr[:, 2]), cast(Any, y_pred_arr[:, 2])))
    rmse_6h = float(np.sqrt(mean_squared_error(cast(Any, y_true_arr[:, 2]), cast(Any, y_pred_arr[:, 2]))))
    r2_6h = float(r2_score(cast(Any, y_true_arr[:, 2]), cast(Any, y_pred_arr[:, 2])))
    
    return {
        "mae": round(mae_overall, 3),
        "rmse": round(rmse_overall, 3),
        "r2": round(r2_overall, 4),
        "horizons": {
            "1h": {"mae": round(mae_1h, 3), "rmse": round(rmse_1h, 3), "r2": round(r2_1h, 4)},
            "3h": {"mae": round(mae_3h, 3), "rmse": round(rmse_3h, 3), "r2": round(r2_3h, 4)},
            "6h": {"mae": round(mae_6h, 3), "rmse": round(rmse_6h, 3), "r2": round(r2_6h, 4)},
        }
    }

def train_moisture_forecasting_models():
    """Main training routine: trains candidates, evaluates, serializes best model."""
    print("=" * 70)
    print("IRRIGATEWISE ML PIPELINE: SOIL MOISTURE FORECASTING")
    print("=" * 70)
    
    df = load_and_preprocess_dataset()
    print(f"Loaded dataset: {len(df)} total time-series observations.")
    
    X_train, y_train, X_val, y_val, X_test, y_test = chronological_split(df)
    print(f"Split sizes: Train={len(X_train)} (70%), Val={len(X_val)} (15%), Test={len(X_test)} (15%)")
    
    # Feature scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    candidate_models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=120,
            max_depth=14,
            min_samples_split=4,
            random_state=42,
            n_jobs=-1
        ),
        "Gradient Boosting": MultiOutputRegressor(
            cast(
                Any,
                HistGradientBoostingRegressor(
                    max_iter=120,
                    max_depth=8,
                    learning_rate=0.08,
                    random_state=42,
                ),
            )
        ),
    }
    
    comparison_results = []
    trained_estimators = {}
    
    for name, model in candidate_models.items():
        print(f"\n[Training] {name}...")
        
        # Linear Regression benefits from scaling; tree models work on scaled or unscaled
        model.fit(X_train_scaled, y_train)
        trained_estimators[name] = model
        
        # Evaluate on Test Set
        y_test_pred = model.predict(X_test_scaled)
        metrics = evaluate_predictions(y_test, y_test_pred)
        
        print(f"  -> Test MAE:  {metrics['mae']:.3f} % moisture")
        print(f"  -> Test RMSE: {metrics['rmse']:.3f} % moisture")
        print(f"  -> Test R²:   {metrics['r2']:.4f}")
        print(f"     1h Forecast: MAE={metrics['horizons']['1h']['mae']:.2f}, R²={metrics['horizons']['1h']['r2']:.4f}")
        print(f"     3h Forecast: MAE={metrics['horizons']['3h']['mae']:.2f}, R²={metrics['horizons']['3h']['r2']:.4f}")
        print(f"     6h Forecast: MAE={metrics['horizons']['6h']['mae']:.2f}, R²={metrics['horizons']['6h']['r2']:.4f}")
        
        comparison_results.append({
            "name": name,
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "r2": metrics["r2"],
            "horizons": metrics["horizons"]
        })
        
    # Select Best Model based on Lowest RMSE / Highest R2
    best_candidate = max(comparison_results, key=lambda x: x["r2"])
    best_name = best_candidate["name"]
    best_model = trained_estimators[best_name]
    
    print("\n" + "=" * 70)
    print(f"BEST PERFORMING MODEL: {best_name} (R² = {best_candidate['r2']:.4f}, RMSE = {best_candidate['rmse']:.3f})")
    print("=" * 70)
    
    # Feature importance extraction
    feature_importance_dict = {}
    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
        sorted_indices = np.argsort(importances)[::-1]
        for idx in sorted_indices:
            feature_importance_dict[FEATURE_COLUMNS[idx]] = round(float(importances[idx]), 4)
    elif "Random Forest" in trained_estimators and hasattr(trained_estimators["Random Forest"], "feature_importances_"):
        # Use tree-based ensemble importances from Random Forest
        rf_model = trained_estimators["Random Forest"]
        importances = rf_model.feature_importances_
        sorted_indices = np.argsort(importances)[::-1]
        for idx in sorted_indices:
            feature_importance_dict[FEATURE_COLUMNS[idx]] = round(float(importances[idx]), 4)
    else:
        for col in FEATURE_COLUMNS:
            feature_importance_dict[col] = round(1.0 / len(FEATURE_COLUMNS), 4)
                
    # 1. Save model comparison JSON
    comparison_file = os.path.join(ARTIFACTS_DIR, "model_comparison.json")
    comparison_payload = {
        "dataset": "Development/Simulation (Physics-Informed with Hydrogel)",
        "evaluation_date": datetime.now(timezone.utc).isoformat(),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "target_horizons": ["1h", "3h", "6h"],
        "best_model": best_name,
        "models": comparison_results,
        "feature_importance": feature_importance_dict
    }
    with open(comparison_file, "w", encoding="utf-8") as f:
        json.dump(comparison_payload, f, indent=2)
    print(f"Saved model comparison to: {comparison_file}")
    
    # 2. Serialize Best Model Artifact
    artifact_path = os.path.join(ARTIFACTS_DIR, "moisture_model.joblib")
    model_artifact = {
        "model_name": best_name,
        "version": "v1.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "features": FEATURE_COLUMNS,
        "targets": TARGET_COLUMNS,
        "metrics": best_candidate,
        "feature_importance": feature_importance_dict,
        "scaler": scaler,
        "model": best_model
    }
    joblib.dump(model_artifact, artifact_path)
    print(f"Saved production model artifact to: {artifact_path}")
    
    return best_candidate

if __name__ == "__main__":
    train_moisture_forecasting_models()
