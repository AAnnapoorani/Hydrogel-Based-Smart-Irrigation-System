"""Unit test suite for Deep Learning Plant Pathology and Pest Computer Vision Pipeline."""

import os
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.plant_health_service import PlantHealthService
from ml.evaluate_dl_model import generate_dl_evaluation_report
from ml.yolo_pest_detector import yolo_pest_engine


def test_deep_learning_3_models_evaluation():
    report = generate_dl_evaluation_report()
    assert report is not None
    assert "models_comparison" in report
    models = report["models_comparison"]
    assert len(models) == 3

    model_ids = [m["model_id"] for m in models]
    assert "mobilenet_v3_small" in model_ids
    assert "efficientnet_b0" in model_ids
    assert "resnet_50" in model_ids

    mobilenet = next(m for m in models if m["model_id"] == "mobilenet_v3_small")
    assert mobilenet["status"] == "Active (Deployed)"
    assert 90.0 <= mobilenet["top1_accuracy"] <= 95.0
    assert mobilenet["latency_ms"] < 20.0
    assert mobilenet["parameters_million"] < 2.0

    assert "comparative_training_history" in report
    comp_hist = report["comparative_training_history"]
    assert len(comp_hist["mobilenet_v3"]) == 15
    assert len(comp_hist["efficientnet_b0"]) == 15
    assert len(comp_hist["resnet_50"]) == 15


def test_pest_detection_filename_independence():
    """Verifies that filename and directory paths cannot influence diagnostic outputs."""
    arr = np.zeros((300, 300, 3), dtype=np.uint8)
    arr[:, :] = [45, 140, 50]
    for i in range(10):
        x = 30 + (i % 5) * 50
        y = 50 + (i // 5) * 80
        arr[y:y+12, x:x+10] = [245, 248, 250]

    img = Image.fromarray(arr)
    filenames = [
        "IMG_9823.jpg",
        "val/23/armyworm.jpg",
        "sample_spider_mite.png",
        "healthy_clean_leaf.jpg",
        None
    ]

    results = [PlantHealthService.analyze_pests(img, filename=fn) for fn in filenames]

    base = results[0]
    for res in results[1:]:
        assert res.status == base.status
        assert res.primary_pest == base.primary_pest
        assert res.is_conclusive == base.is_conclusive
        assert res.confidence == base.confidence
        assert res.pest_count == base.pest_count
        assert res.bounding_boxes == base.bounding_boxes
        assert res.annotated_image_base64 == base.annotated_image_base64


def test_pest_detection_returns_inconclusive_without_validated_model():
    """Verifies that in Phase 1, anomalous foliage returns honest inconclusive status."""
    arr = np.zeros((300, 300, 3), dtype=np.uint8)
    arr[:, :] = [45, 140, 50]
    for i in range(10):
        x = 30 + (i % 5) * 50
        y = 50 + (i // 5) * 80
        arr[y:y+12, x:x+10] = [245, 248, 250]

    img = Image.fromarray(arr)
    res = PlantHealthService.analyze_pests(img, filename="camera_sample_01.jpg")

    assert res.status == "inconclusive"
    assert res.is_conclusive is False
    assert res.confidence == 0.0
    assert res.bounding_boxes == []
    assert res.pest_count is None
    assert res.annotated_image_base64 is None
    assert res.primary_pest == "Undetermined / Inconclusive Visual Anomaly"


def test_clean_canopy_screening_humility():
    """Verifies that clean foliage returns inconclusive without claiming confirmed pest absence."""
    arr = np.zeros((300, 300, 3), dtype=np.uint8)
    arr[:, :] = [45, 155, 55]  # Uniform green leaf
    img = Image.fromarray(arr)
    res = PlantHealthService.analyze_pests(img, filename="canopy_capture.jpg")

    assert res.status == "inconclusive"
    assert res.is_conclusive is False
    assert res.confidence == 0.0
    assert res.primary_pest == "No Macroscopic Anomalies Observed (Screening Only)"
    assert res.pest_count is None
    assert res.bounding_boxes == []
    assert res.annotated_image_base64 is None


def test_service_layer_prevents_silent_aphid_overwrite():
    """Verifies that non-aphid visual anomalies are never silently overwritten to Aphids."""
    arr = np.zeros((400, 400, 3), dtype=np.uint8)
    arr[:, :] = [50, 145, 55]
    for i in range(15):
        x = 30 + (i % 5) * 65
        y = 40 + (i // 5) * 90
        arr[y:y+8, x:x+8] = [215, 60, 25]  # Red/amber specks

    img = Image.fromarray(arr)
    res = PlantHealthService.analyze_pests(img, filename="camera_feed_frame.jpg")

    assert res.primary_pest != "Aphids (Greenfly / Blackfly)"
    assert res.status == "inconclusive"
    assert res.is_conclusive is False
    assert res.pest_count is None


def test_universal_pest_detector_engine_phase1_behavior():
    """Verifies UniversalPestDetector engine disables unused YOLO and emits honest screening."""
    assert yolo_pest_engine.yolo_model is None
    assert yolo_pest_engine.is_available is False

    arr = np.zeros((300, 300, 3), dtype=np.uint8)
    arr[:, :] = [45, 140, 50]
    img = Image.fromarray(arr)
    yolo_res = yolo_pest_engine.detect_pests(img)

    assert yolo_res["status"] == "inconclusive"
    assert yolo_res["confidence"] == 0.0
    assert yolo_res["pest_count"] is None
    assert yolo_res["bounding_boxes"] == []
    assert yolo_res["annotated_image_base64"] is None
    assert "Phase 2" in yolo_res["model_architecture"]
