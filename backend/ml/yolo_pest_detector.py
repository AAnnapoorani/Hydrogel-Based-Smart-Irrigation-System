"""Universal Multi-Pest Localizer & Detection Engine.

Detects agricultural pest categories from the IP102 benchmark dataset
(Xiaoping Wu et al., CVPR 2019) and garden container pests.

Phase 1 Specification:
- Unvalidated heuristic bounding boxes and fabricated confidence formulas are disabled.
- Filename and directory sniffing is completely purged.
- Unused YOLO weight initialization is disabled to eliminate dead COCO weight loading.
- Returns honest inconclusive screening results pending Phase 2 classifier training.
"""

import os
import io
import time
from typing import Dict, List, Any, Optional
from PIL import Image
import numpy as np
import cv2

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

from ml.ip102_classes import IP102_CLASSES, PEST_FAMILY_CONFIG

MODEL_PATH = os.path.join(os.path.dirname(__file__), "yolov8n.pt")


class UniversalPestDetector:
    """Multi-Pest Localization and Taxonomy Detection Engine."""

    _instance: Optional["UniversalPestDetector"] = None

    def __init__(self):
        self.yolo_model = None
        self.is_available = False
        # Phase 1: Unused YOLO initialization is disabled to avoid loading COCO weights into memory
        # self._init_yolo()

    @classmethod
    def get_instance(cls) -> "UniversalPestDetector":
        if cls._instance is None:
            cls._instance = UniversalPestDetector()
        return cls._instance

    def _init_yolo(self):
        """Extension point for genuine pest detector initialization in Phase 4."""
        if not HAS_YOLO:
            return
        try:
            if os.path.exists(MODEL_PATH):
                self.yolo_model = YOLO(MODEL_PATH)
            else:
                self.yolo_model = YOLO("yolov8n.pt")
            self.is_available = True
            print("[UniversalPestDetector] YOLOv8-Nano backbone loaded successfully.")
        except Exception as e:
            print(f"[UniversalPestDetector] Warning: YOLO init fallback: {e}")
            self.is_available = False

    def detect_pests(
        self,
        image: Image.Image,
        conf_threshold: float = 0.25,
        filename: Optional[str] = None,
        plant_hint: Optional[str] = None,
        symptom_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs preliminary optical screening across pest families.

        In Phase 1, unvalidated heuristic bounding boxes and fabricated confidence
        formulas are completely disabled. Uploaded filenames and directory paths are ignored.
        Returns honest inconclusive screening results.
        """
        start_time = time.perf_counter()
        img_rgb = image.convert("RGB")
        img_np = np.array(img_rgb, dtype=np.float32) / 255.0
        r = img_np[:, :, 0]
        g = img_np[:, :, 1]
        b = img_np[:, :, 2]

        # Preliminary optical screening: inspect foliage coloration and macroscopic anomalies
        # (Uploaded filenames and directory paths are strictly ignored)
        exg = 2.0 * g - r - b
        green_mask = (g > r) & (g > b) & (g > 0.2)
        green_ratio = float(np.mean(green_mask))

        non_green_lesions = (exg < 0.05) & (np.maximum(r, b) > 0.25)
        lesion_ratio = float(np.mean(non_green_lesions))

        if green_ratio > 0.60 and lesion_ratio < 0.005:
            primary_name = "No Macroscopic Anomalies Observed (Screening Only)"
            pest_key = "clean_canopy"
            detection_type = "Preliminary Optical Screening (Clean Canopy)"
        else:
            primary_name = "Undetermined / Inconclusive Visual Anomaly"
            pest_key = "visual_anomaly"
            detection_type = "Preliminary Optical Screening (Rule-Based)"

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 1)

        return {
            "status": "inconclusive",
            "primary_pest": primary_name,
            "pest_key": pest_key,
            "specific_class_id": None,
            "specific_class_name": primary_name,
            "confidence": 0.0,
            "pest_count": None,
            "bounding_boxes": [],
            "annotated_image_base64": None,
            "latency_ms": latency_ms,
            "detection_type": detection_type,
            "model_architecture": "Preliminary Optical Screening (Deep Learning Classifier Pending - Phase 2)"
        }


# Global singleton instance
yolo_pest_engine = UniversalPestDetector.get_instance()
