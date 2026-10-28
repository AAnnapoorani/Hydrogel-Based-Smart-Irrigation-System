"""Model Registry and Version Management for IRRIGATEWISE.

Manages model versions, evaluation metrics, active production deployment pointers,
and metadata persistence in PostgreSQL ml_model_versions table.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
import models

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")

class ModelRegistry:
    @staticmethod
    def get_comparison_data() -> Dict[str, Any]:
        """Loads model comparison artifacts containing genuine training metrics."""
        path = os.path.join(ARTIFACTS_DIR, "model_comparison.json")
        if not os.path.exists(path):
            return {
                "dataset": "Development/Simulation (Uninitialized)",
                "evaluation_date": datetime.now(timezone.utc).isoformat(),
                "best_model": "None",
                "models": []
            }
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def get_evaluation_points_data() -> Dict[str, Any]:
        """Loads genuine test evaluation points comparing actual vs predicted on held-out test split."""
        path = os.path.join(ARTIFACTS_DIR, "evaluation_points.json")
        if not os.path.exists(path):
            return {
                "metadata": {
                    "model_name": "Multi-Output Gradient Boosting Regressor",
                    "status": "Unavailable",
                    "total_dataset_samples": 8628,
                    "test_samples": 1295,
                },
                "samples": [],
                "full_residuals": {"res_1h": [], "res_3h": [], "res_6h": []}
            }
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def sync_to_database(db: Session):
        """Syncs filesystem model comparison metrics into PostgreSQL ml_model_versions table."""
        comp = ModelRegistry.get_comparison_data()
        for m in comp.get("models", []):
            name = m["name"]
            version_tag = f"{name.lower().replace(' ', '_')}_v1.0"
            existing = db.query(models.MLModelVersion).filter(
                models.MLModelVersion.version_tag == version_tag
            ).first()
            
            is_active = 1 if name == comp.get("best_model") else 0
            
            if existing:
                existing.mae = m.get("mae")
                existing.rmse = m.get("rmse")
                existing.r2_score = m.get("r2")
                setattr(existing, "is_active", is_active)
            else:
                db_record = models.MLModelVersion(
                    model_name=name,
                    version_tag=version_tag,
                    algorithm=name,
                    target_variable="future_soil_moisture (1h, 3h, 6h)",
                    mae=m.get("mae"),
                    rmse=m.get("rmse"),
                    r2_score=m.get("r2"),
                    hyperparameters=json.dumps(m.get("horizons", {})),
                    is_active=is_active,
                )
                db.add(db_record)
        db.commit()

    @staticmethod
    def get_active_model_details(db: Optional[Session] = None) -> Dict[str, Any]:
        """Retrieves details of the currently deployed production model."""
        comp = ModelRegistry.get_comparison_data()
        best_name = comp.get("best_model", "Gradient Boosting")
        best_metrics = next((m for m in comp.get("models", []) if m["name"] == best_name), {})
        
        return {
            "model_name": best_name,
            "version": "v1.0",
            "algorithm": best_name,
            "target": "future_soil_moisture (1h, 3h, 6h)",
            "metrics": best_metrics,
            "feature_importance": comp.get("feature_importance", {}),
            "status": "PRODUCTION_ACTIVE",
            "last_evaluated": comp.get("evaluation_date")
        }
