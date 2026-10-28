"""Crop Recommendation ML Classification Pipeline.

Upgrades the heuristic rule-based crop matching into a machine-learning classifier.
Trains and compares:
1. Decision Tree Classifier
2. Random Forest Classifier
3. Gradient Boosting Classifier

Features:
- Nitrogen (N)
- Phosphorus (P)
- Potassium (K)
- pH
- Organic Carbon (OC)
- Temperature
- Humidity
- Rainfall
- Soil Texture (One-Hot Encoded)

Target:
- Crop Category (Samba Rice, Sugarcane, Black Gram, Groundnut, Cotton, Maize, Green Gram, Finger Millet)
"""

import os
# pyrefly: ignore [missing-import]
import joblib
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import pandas as pd
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from sklearn.model_selection import train_test_split
# pyrefly: ignore [missing-import]
from sklearn.tree import DecisionTreeClassifier
# pyrefly: ignore [missing-import]
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
# pyrefly: ignore [missing-import]
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

CROPS = [
    "Bush Tomato",
    "Cherry Tomato",
    "Green Chilli",
    "Capsicum",
    "Brinjal",
    "Okra",
    "Bush French Beans",
    "Amaranth Keerai",
    "Indian Spinach",
    "Spearmint",
    "Coriander",
    "Curry Leaf",
    "White Radish",
    "Strawberry",
]

def load_or_generate_terrace_crop_dataset(samples_per_crop: int = 250) -> pd.DataFrame:
    """Loads authentic terrace garden dataset or generates realistic agronomic clusters."""
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "soil_and_crops", "terrace_crop_recommendation.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        if len(df) > 0 and "crop" in df.columns:
            return df

    np.random.seed(42)
    rows = []
    
    profiles = {
        "Bush Tomato":       (115, 12, 55, 8, 220, 20, 6.4, 0.3, 1.10, 0.15, 28, 3, 70, 7, 100, 20, ["loam", "clay", "sandy"], [0.65, 0.25, 0.10]),
        "Cherry Tomato":     (105, 10, 48, 7, 195, 18, 6.4, 0.3, 1.05, 0.12, 26, 3, 65, 6, 85, 18, ["loam", "clay", "sandy"], [0.70, 0.20, 0.10]),
        "Green Chilli":      (90, 10, 42, 6, 150, 15, 6.5, 0.4, 0.85, 0.10, 30, 4, 60, 8, 70, 15, ["loam", "sandy", "clay"], [0.60, 0.30, 0.10]),
        "Capsicum":          (105, 10, 50, 6, 185, 18, 6.6, 0.3, 0.95, 0.12, 25, 3, 70, 6, 80, 15, ["loam", "clay", "sandy"], [0.65, 0.25, 0.10]),
        "Brinjal":           (110, 12, 48, 7, 170, 18, 6.6, 0.4, 1.00, 0.14, 29, 3, 68, 7, 95, 20, ["loam", "clay", "sandy"], [0.60, 0.30, 0.10]),
        "Okra":              (75, 9, 35, 5, 125, 14, 6.8, 0.4, 0.75, 0.10, 32, 4, 58, 8, 75, 18, ["loam", "sandy", "clay"], [0.55, 0.30, 0.15]),
        "Bush French Beans": (45, 7, 50, 7, 105, 12, 6.4, 0.3, 0.85, 0.12, 24, 3, 62, 6, 65, 15, ["loam", "sandy", "clay"], [0.65, 0.25, 0.10]),
        "Amaranth Keerai":   (100, 10, 30, 5, 115, 12, 6.7, 0.4, 1.10, 0.15, 31, 3, 72, 7, 70, 15, ["loam", "clay", "sandy"], [0.60, 0.25, 0.15]),
        "Indian Spinach":    (95, 10, 35, 5, 110, 12, 6.6, 0.3, 1.15, 0.15, 25, 3, 75, 6, 60, 12, ["loam", "clay", "sandy"], [0.70, 0.20, 0.10]),
        "Spearmint":         (80, 9, 28, 4, 90, 10, 6.5, 0.3, 1.20, 0.16, 26, 3, 72, 7, 50, 10, ["loam", "clay", "sandy"], [0.70, 0.20, 0.10]),
        "Coriander":         (65, 8, 26, 4, 80, 10, 6.6, 0.3, 0.90, 0.12, 23, 3, 62, 6, 45, 10, ["loam", "sandy", "clay"], [0.65, 0.25, 0.10]),
        "Curry Leaf":        (78, 9, 35, 5, 135, 15, 6.8, 0.4, 0.95, 0.14, 31, 4, 60, 8, 90, 20, ["loam", "clay", "sandy"], [0.60, 0.25, 0.15]),
        "White Radish":      (60, 8, 48, 6, 130, 14, 6.4, 0.3, 0.80, 0.10, 23, 3, 60, 6, 50, 12, ["sandy", "loam", "clay"], [0.55, 0.35, 0.10]),
        "Strawberry":        (55, 7, 55, 7, 175, 18, 6.0, 0.3, 1.30, 0.18, 21, 3, 68, 6, 40, 10, ["loam", "sandy", "clay"], [0.65, 0.25, 0.10]),
    }
    
    for crop, prof in profiles.items():
        n_m, n_s, p_m, p_s, k_m, k_s, ph_m, ph_s, oc_m, oc_s, t_m, t_s, h_m, h_s, r_m, r_s, soils, soil_probs = prof
        for _ in range(samples_per_crop):
            rows.append({
                "nitrogen": round(float(np.clip(np.random.normal(n_m, n_s), 15, 180)), 1),
                "phosphorus": round(float(np.clip(np.random.normal(p_m, p_s), 10, 100)), 1),
                "potassium": round(float(np.clip(np.random.normal(k_m, k_s), 40, 320)), 1),
                "ph": round(float(np.clip(np.random.normal(ph_m, ph_s), 4.8, 8.5)), 2),
                "organic_carbon": round(float(np.clip(np.random.normal(oc_m, oc_s), 0.25, 2.0)), 2),
                "temperature": round(float(np.clip(np.random.normal(t_m, t_s), 15, 42)), 1),
                "humidity": round(float(np.clip(np.random.normal(h_m, h_s), 30, 95)), 1),
                "rainfall": round(float(np.clip(np.random.normal(r_m, r_s), 10, 250)), 1),
                "soil_type": np.random.choice(soils, p=soil_probs),
                "crop": crop
            })
            
    df = pd.DataFrame(rows)
    return df

CROP_FEATURE_COLUMNS = [
    "nitrogen", "phosphorus", "potassium", "ph", "organic_carbon",
    "temperature", "humidity", "rainfall",
    "soil_clay", "soil_loam", "soil_sandy"
]

def preprocess_crop_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    df = df.copy()
    st = df["soil_type"].astype(str).str.lower()
    df["soil_clay"] = (st == "clay").astype(int)
    df["soil_loam"] = (st == "loam").astype(int)
    df["soil_sandy"] = (st == "sandy").astype(int)
    
    X = np.asarray(df[CROP_FEATURE_COLUMNS].values)
    y = np.asarray(df["crop"].values)
    return X, y

def train_crop_classifier():
    """Trains, compares, and serializes the crop recommendation ML model."""
    print("=" * 70)
    print("IRRIGATEWISE ML PIPELINE: TERRACE CROP RECOMMENDATION CLASSIFIER")
    print("=" * 70)
    
    df = load_or_generate_terrace_crop_dataset(samples_per_crop=250)
    X, y = preprocess_crop_features(df)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=list(y)
    )
    print(f"Total Dataset: {len(df)} samples across {len(set(y))} terrace crop classes.")
    print(f"Dataset split: Train={len(X_train)} samples, Test={len(X_test)} samples.")
    
    candidates = {
        "Decision Tree": DecisionTreeClassifier(max_depth=8, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=80, max_depth=4, random_state=42)
    }
    
    results = []
    trained = {}
    
    for name, model in candidates.items():
        print(f"\n[Training] {name} Classifier...")
        model.fit(X_train, y_train)
        trained[name] = model
        
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average="weighted")
        rec = recall_score(y_test, y_pred, average="weighted")
        f1 = f1_score(y_test, y_pred, average="weighted")
        
        print(f"  -> Accuracy:  {acc * 100:.2f}%")
        print(f"  -> Precision: {prec:.4f}")
        print(f"  -> Recall:    {rec:.4f}")
        print(f"  -> F1-Score:  {f1:.4f}")
        
        results.append({
            "name": name,
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4)
        })
        
    best_candidate = max(results, key=lambda x: x["f1_score"])
    best_name = best_candidate["name"]
    best_model = trained[best_name]
    
    print("\n" + "=" * 70)
    print(f"BEST CROP CLASSIFIER: {best_name} (Accuracy: {best_candidate['accuracy']*100:.2f}%, F1: {best_candidate['f1_score']:.4f})")
    print("=" * 70)
    
    # Save model artifact
    artifact_path = os.path.join(ARTIFACTS_DIR, "crop_model.joblib")
    artifact = {
        "model_name": best_name,
        "version": "v1.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "classes": list(best_model.classes_),
        "features": CROP_FEATURE_COLUMNS,
        "metrics": best_candidate,
        "model": best_model
    }
    joblib.dump(artifact, artifact_path)
    print(f"Saved crop model artifact to: {artifact_path}")
    return best_candidate

class CropRecommender:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CropRecommender, cls).__new__(cls)
            cls._instance._load()
        return cls._instance
        
    def _load(self):
        path = os.path.join(ARTIFACTS_DIR, "crop_model.joblib")
        if not os.path.exists(path):
            train_crop_classifier()
        self.artifact = joblib.load(path)
        self.model = self.artifact["model"]
        self.classes = self.artifact["classes"]
        self.model_name = self.artifact["model_name"]
        
    def predict(self, n: float, p: float, k: float, ph: float, oc: float,
                temp: float = 30.0, hum: float = 70.0, rain: float = 100.0,
                soil_type: str = "loam") -> Dict[str, Any]:
        st = soil_type.lower()
        is_clay = 1 if st == "clay" else 0
        is_loam = 1 if st == "loam" else 0
        is_sandy = 1 if st == "sandy" else 0
        
        x = np.array([
            n, p, k, ph, oc, temp, hum, rain,
            is_clay, is_loam, is_sandy
        ], dtype=np.float32).reshape(1, -1)
        
        probs = self.model.predict_proba(x)[0]
        top_indices = np.argsort(probs)[::-1]
        
        top_candidates = []
        for idx in top_indices[:4]:
            top_candidates.append({
                "crop": self.classes[idx],
                "probability": round(float(probs[idx]), 3)
            })
            
        best_crop = self.classes[top_indices[0]]
        best_prob = round(float(probs[top_indices[0]]), 3)
        
        return {
            "recommended_crop": best_crop,
            "confidence": best_prob,
            "top_candidates": top_candidates,
            "model_name": self.model_name
        }

if __name__ == "__main__":
    from typing import Tuple
    train_crop_classifier()
