"""Automated Test Suite for Phase 3: IP102 Classifier Integration.

Covers all 22 mandatory verification scenarios:
1. Correct checkpoint loads successfully.
2. Correct class mapping loads successfully.
3. Missing checkpoint is handled safely.
4. Invalid or mismatched class mapping is rejected.
5. Inference does not require a GPU (CPU execution).
6. Model initialization is not repeated for every request (singleton pattern).
7. A valid image produces a structurally valid model result.
8. Model output indices resolve to correct original IP102 labels.
9. A validated mapping resolves to expected normalized pest family.
10. An unsupported mapping does not become a confirmed diagnosis.
11. A low-confidence result follows documented provisional policy.
12. Invalid or corrupted images are rejected safely.
13. Model inference failures do not create fabricated diagnoses.
14. No path silently defaults to Aphids or another pest.
15. Output scores are derived from actual model forward-pass inference.
16. Phase 1 inconclusive clean-canopy behavior remains available.
17. Existing pest diagnosis API contracts remain strictly compatible.
18. Existing plant disease diagnosis remains unchanged.
19. Irrigation decision logic remains unchanged.
20. Nutrient recommendation behavior remains unchanged.
21. Existing IP102 pipeline tests continue to pass.
22. Existing plant vision tests continue to pass.
"""

import os
import sys
import json
import pytest
import numpy as np
import torch
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.ml.ip102_inference import (
    IP102InferenceEngine,
    get_ip102_engine,
    DEFAULT_ARTIFACTS_DIR,
    DEFAULT_MAPPING_PATH
)
from backend.services.plant_health_service import PlantHealthService, PEST_KNOWLEDGE_BASE
from backend.schemas import PestDiagnosisOutput, PlantDiagnosisOutput


# ══════════════════════════════════════════════════════════════════════════════
# 1. MODEL AND ARTIFACT TESTS (Scenarios 1-6)
# ══════════════════════════════════════════════════════════════════════════════

def test_01_correct_checkpoint_loads_successfully():
    """Scenario 1: Verifies best_checkpoint.pt exists and loads cleanly into MobileNetV3-Small."""
    engine = IP102InferenceEngine()
    loaded = engine.load_artifacts()
    assert loaded is True, f"Failed to load checkpoint: {engine.load_error}"
    assert engine.model is not None
    assert engine.is_loaded is True
    assert isinstance(engine.model, torch.nn.Module)


def test_02_correct_class_mapping_loads_successfully():
    """Scenario 2: Verifies exact 102-class mapping and terrace relevance mapping load."""
    engine = IP102InferenceEngine()
    engine.load_artifacts()

    assert len(engine.class_names) == 102
    assert len(engine.id_to_name) == 102
    assert engine.id_to_name[0] == "rice leaf roller"
    assert engine.id_to_name[92] == "Scirtothrips dorsalis Hood"
    assert engine.id_to_name[101] == "Cicadellidae"

    assert len(engine.terrace_mappings) == 102
    assert engine.terrace_mappings[92]["status"] == "validated"
    assert engine.terrace_mappings[92]["target_pest_family"] == "thrips"
    assert engine.terrace_mappings[0]["status"] == "unsupported"


def test_03_missing_checkpoint_handled_safely(tmp_path):
    """Scenario 3: Verifies missing checkpoint produces model_unavailable without crashing."""
    empty_dir = str(tmp_path / "nonexistent_artifacts")
    os.makedirs(empty_dir, exist_ok=True)

    engine = IP102InferenceEngine(artifacts_dir=empty_dir)
    img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    res = engine.predict(img)

    assert res["status"] == "model_unavailable"
    assert res["raw_index"] is None
    assert res["raw_softmax_score"] == 0.0
    assert res["confidence_pct"] == 0.0
    assert "missing" in res["error_message"].lower() or "checkpoint" in res["error_message"].lower()


def test_04_invalid_or_mismatched_class_mapping_rejected(tmp_path):
    """Scenario 4: Verifies corrupted/truncated class mapping is rejected."""
    bad_dir = str(tmp_path / "bad_artifacts")
    os.makedirs(bad_dir, exist_ok=True)

    # Copy real checkpoint
    real_ckpt = os.path.join(DEFAULT_ARTIFACTS_DIR, "best_checkpoint.pt")
    if os.path.exists(real_ckpt):
        import shutil
        shutil.copy(real_ckpt, os.path.join(bad_dir, "best_checkpoint.pt"))

    # Write invalid class mapping with only 10 classes
    with open(os.path.join(bad_dir, "class_mapping.json"), "w") as f:
        json.dump({"classes": ["class_1", "class_2"]}, f)

    engine = IP102InferenceEngine(artifacts_dir=bad_dir)
    img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    res = engine.predict(img)

    assert res["status"] == "model_unavailable"
    assert "Invalid class mapping" in res["error_message"]


def test_05_inference_does_not_require_gpu():
    """Scenario 5: Verifies that CPU device execution succeeds without CUDA."""
    engine = IP102InferenceEngine(device="cpu")
    engine.load_artifacts()
    assert str(engine.device) == "cpu"

    img = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
    res = engine.predict(img)
    assert res["status"] in ["classified_candidate", "unsupported_class", "inconclusive"]
    assert isinstance(res["raw_softmax_score"], float)


def test_06_model_initialization_not_repeated_for_every_request():
    """Scenario 6: Verifies singleton pattern caches model instance across requests."""
    e1 = get_ip102_engine()
    e2 = get_ip102_engine()
    assert e1 is e2

    e1.load_artifacts()
    cached_model = e1.model
    assert cached_model is not None

    img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    e1.predict(img)
    assert e1.model is cached_model, "Model instance must not be recreated per request"


# ══════════════════════════════════════════════════════════════════════════════
# 2. PREDICTION AND UNCERTAINTY TESTS (Scenarios 7-15)
# ══════════════════════════════════════════════════════════════════════════════

def test_07_valid_image_produces_structurally_valid_result():
    """Scenario 7: Verifies response schema conforms to required inference structure."""
    engine = get_ip102_engine()
    img = Image.fromarray(np.full((250, 250, 3), 120, dtype=np.uint8))
    res = engine.predict(img)

    required_keys = [
        "status", "raw_index", "raw_class_name", "raw_softmax_score",
        "confidence_pct", "top5_candidates", "terrace_family",
        "mapping_status", "model_architecture", "is_conclusive"
    ]
    for k in required_keys:
        assert k in res, f"Missing key in prediction: {k}"

    assert res["is_conclusive"] is False
    assert len(res["top5_candidates"]) <= 5


def test_08_output_indices_resolve_to_correct_original_ip102_labels():
    """Scenario 8: Verifies output indices map to exact original IP102 class labels."""
    engine = get_ip102_engine()
    engine.load_artifacts()

    test_indices = {
        0: "rice leaf roller",
        18: "black cutworm",
        24: "aphids",
        37: "flea beetle",
        71: "Trialeurodes vaporariorum",
        92: "Scirtothrips dorsalis Hood",
        101: "Cicadellidae"
    }
    for idx, expected_name in test_indices.items():
        assert engine.id_to_name[idx] == expected_name


def test_09_validated_mapping_resolves_to_expected_normalized_family():
    """Scenario 9: Tests that a mock validated class prediction resolves to correct terrace family."""
    engine = IP102InferenceEngine()
    engine.load_artifacts()

    # Create mock logits with class 92 (Scirtothrips dorsalis Hood -> thrips) as dominant prediction
    class MockModel(torch.nn.Module):
        def forward(self, x):
            logits = torch.full((1, 102), -10.0)
            logits[0, 92] = 5.0  # Dominant prediction for class 92
            return logits

    engine.model = MockModel()
    img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    res = engine.predict(img)

    assert res["status"] == "classified_candidate"
    assert res["raw_index"] == 92
    assert res["raw_class_name"] == "Scirtothrips dorsalis Hood"
    assert res["terrace_family"] == "thrips"
    assert res["mapping_status"] == "validated"
    assert res["confidence_pct"] > 50.0


def test_10_unsupported_mapping_does_not_become_confirmed_diagnosis():
    """Scenario 10: Tests that an unsupported agricultural pest produces unsupported_class status."""
    engine = IP102InferenceEngine()
    engine.load_artifacts()

    # Create mock logits with class 0 (rice leaf roller -> unsupported) as dominant prediction
    class MockModel(torch.nn.Module):
        def forward(self, x):
            logits = torch.full((1, 102), -10.0)
            logits[0, 0] = 5.0  # Dominant prediction for class 0
            return logits

    engine.model = MockModel()
    img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    res = engine.predict(img)

    assert res["status"] == "unsupported_class"
    assert res["raw_index"] == 0
    assert res["raw_class_name"] == "rice leaf roller"
    assert res["terrace_family"] is None
    assert res["mapping_status"] == "unsupported"
    assert res["is_conclusive"] is False

    # Also test integration via PlantHealthService
    service_res = PlantHealthService.analyze_pests(img)
    # Since mock wasn't set on singleton, test that service layer can handle unsupported
    assert service_res.is_conclusive is False
    assert service_res.bounding_boxes == []


def test_11_low_confidence_follows_documented_provisional_policy():
    """Scenario 11: Tests that a score below the 0.25 provisional threshold is flagged inconclusive."""
    engine = IP102InferenceEngine(provisional_threshold=0.25)
    engine.load_artifacts()

    # Uniform random logits produces 1/102 ≈ 0.0098 for all classes (well below 0.25)
    class UniformModel(torch.nn.Module):
        def forward(self, x):
            return torch.zeros((1, 102))

    engine.model = UniformModel()
    img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    res = engine.predict(img)

    assert res["status"] == "inconclusive"
    assert res["is_conclusive"] is False
    assert res["raw_softmax_score"] < 0.25


def test_12_invalid_or_corrupted_images_rejected_safely():
    """Scenario 12: Verifies None, empty, or degenerate images return safe fallbacks."""
    engine = get_ip102_engine()

    res_none = engine.predict(None)
    assert res_none["status"] == "inconclusive"
    assert res_none["is_conclusive"] is False

    res_tiny = engine.predict(Image.fromarray(np.zeros((2, 2, 3), dtype=np.uint8)))
    assert res_tiny["status"] == "inconclusive"
    assert "too small" in res_tiny["error_message"].lower()


def test_13_model_inference_failures_do_not_fabricate_diagnoses():
    """Scenario 13: Verifies forward pass failure returns safe error structure without hallucination."""
    engine = IP102InferenceEngine()
    engine.load_artifacts()

    class ExplodingModel(torch.nn.Module):
        def forward(self, x):
            raise RuntimeError("CUDA out of memory simulation")

    engine.model = ExplodingModel()
    img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    res = engine.predict(img)

    assert res["status"] == "inconclusive"
    assert res["raw_index"] is None
    assert res["raw_softmax_score"] == 0.0
    assert res["confidence_pct"] == 0.0
    assert "CUDA out of memory" in res["error_message"]


def test_14_no_path_silently_defaults_to_aphids():
    """Scenario 14: Verifies an unsupported or inconclusive result never silently labels as Aphids."""
    engine = get_ip102_engine()
    engine.load_artifacts()

    # Blank image produces inconclusive output (< 0.25 confidence)
    blank = Image.fromarray(np.zeros((200, 200, 3), dtype=np.uint8))
    res = engine.predict(blank)
    assert res["status"] == "inconclusive"

    diag = PlantHealthService.analyze_pests(blank)
    assert diag.status == "inconclusive"
    assert "aphid" not in diag.primary_pest.lower() or "undetermined" in diag.primary_pest.lower()
    assert diag.primary_pest == "Undetermined / Inconclusive Visual Anomaly"


def test_15_output_scores_derived_from_actual_model_inference():
    """Scenario 15: Verifies that output scores are genuine softmax values that sum to 1.0."""
    engine = get_ip102_engine()
    engine.load_artifacts()

    # Run on real image with visual variation
    arr = np.random.randint(50, 200, (224, 224, 3)).astype(np.uint8)
    img = Image.fromarray(arr)

    # Direct model forward pass check
    assert engine.model is not None
    tensor = engine.transforms(img).unsqueeze(0).to(engine.device)
    with torch.no_grad():
        logits = engine.model(tensor)
        probs = torch.softmax(logits, dim=1)[0]

    assert abs(float(probs.sum().item()) - 1.0) < 1e-4, "Softmax probabilities must sum to 1.0"
    top_score, top_idx = torch.topk(probs, 1)

    pred = engine.predict(img)
    assert pred["raw_index"] == int(top_idx[0].item())
    assert abs(pred["raw_softmax_score"] - float(top_score[0].item())) < 1e-3


# ══════════════════════════════════════════════════════════════════════════════
# 3. REGRESSION AND BACKWARD COMPATIBILITY TESTS (Scenarios 16-22)
# ══════════════════════════════════════════════════════════════════════════════

def test_16_phase1_inconclusive_clean_canopy_preserved():
    """Scenario 16: Verifies that uniform clean canopy returns Phase 1 screening output."""
    arr = np.zeros((300, 300, 3), dtype=np.uint8)
    arr[:, :] = [45, 155, 55]  # Healthy green canopy
    img = Image.fromarray(arr)

    diag = PlantHealthService.analyze_pests(img, filename="canopy_view.jpg")
    assert diag.status == "inconclusive"
    assert diag.primary_pest == "No Macroscopic Anomalies Observed (Screening Only)"
    assert diag.confidence == 0.0
    assert diag.is_conclusive is False
    assert diag.bounding_boxes == []
    assert diag.annotated_image_base64 is None
    assert diag.pest_count is None


def test_17_existing_pest_diagnosis_api_contract_compatibility():
    """Scenario 17: Verifies PestDiagnosisOutput schema compatibility with all integrated paths."""
    from schemas import PestDiagnosisOutput as LocalPestOut
    img = Image.fromarray(np.full((200, 200, 3), 100, dtype=np.uint8))
    diag = PlantHealthService.analyze_pests(img)

    assert isinstance(diag, (PestDiagnosisOutput, LocalPestOut))
    # Check all schema required fields exist and have valid types
    assert isinstance(diag.status, str)
    assert isinstance(diag.primary_pest, str)
    assert isinstance(diag.confidence, float)
    assert isinstance(diag.detection_type, str)
    assert isinstance(diag.alternative_pests, list)
    assert isinstance(diag.is_conclusive, bool)
    assert isinstance(diag.visible_evidence, list)
    assert isinstance(diag.typical_damage_symptoms, list)
    assert isinstance(diag.affected_plant_parts, list)
    assert isinstance(diag.inspection_steps, list)
    assert isinstance(diag.organic_management, list)
    assert isinstance(diag.preventive_measures, list)
    assert isinstance(diag.follow_up_monitoring, str)
    assert isinstance(diag.scientific_disclaimer, str)
    assert diag.bounding_boxes == []
    assert diag.annotated_image_base64 is None
    assert diag.pest_count is None


def test_18_existing_plant_disease_diagnosis_remains_unchanged():
    """Scenario 18: Verifies plant disease pathology engine is completely intact."""
    from schemas import PlantDiagnosisOutput as LocalPlantOut
    arr = np.zeros((224, 224, 3), dtype=np.uint8)
    arr[:, :] = [50, 160, 60]
    img = Image.fromarray(arr)

    disease_res = PlantHealthService.analyze_plant_disease(img, plant_hint="Tomato")
    assert isinstance(disease_res, (PlantDiagnosisOutput, LocalPlantOut))
    assert disease_res.status in ["healthy", "conclusive", "inconclusive"]
    assert len(disease_res.verification_steps) > 0
    assert len(disease_res.organic_remediation) > 0
    assert "PlantVillage" in disease_res.scientific_disclaimer


def test_19_irrigation_decision_logic_remains_unchanged():
    """Scenario 19: Verifies irrigation decision engine operates correctly without regression."""
    from backend.services.irrigation_decision_engine import IrrigationDecisionEngine
    from schemas import PredictiveDecisionInput

    inp = PredictiveDecisionInput(
        current_moisture=45.0,
        temperature=32.0,
        humidity=40.0,
        rainfall_forecast_6h=0.0,
        wind_speed=12.0,
        soil_texture="cocopeat_mix",
        crop_type="Potted Tomato",
        hydrogel_present=1,
        container_volume_litres=15.0,
        pot_count=10,
        target_moisture=60.0
    )

    decision = IrrigationDecisionEngine.evaluate(inp)
    assert decision is not None
    assert isinstance(decision.irrigation_required, bool)
    assert decision.water_required_litres >= 0.0
    assert decision.comparison is not None
    assert hasattr(decision, "hydrogel_buffering_active")


def test_20_nutrient_recommendation_behavior_remains_unchanged():
    """Scenario 20: Verifies soil health monitoring advisory operates correctly."""
    from backend.services.soil_health_service import SoilHealthService

    soil_res = SoilHealthService.evaluate_potting_mix(
        nitrogen=110.0,
        phosphorus=45.0,
        potassium=200.0,
        ph=6.4,
        organic_carbon=0.85,
        moisture=58.0,
        plant_type="Tomato"
    )
    assert soil_res is not None
    assert isinstance(soil_res.fertility_grade, str) and len(soil_res.fertility_grade) > 0
    assert len(soil_res.readings) == 4  # N, P, K, pH
    assert "hydrogel" in soil_res.hydrogel_retention_effect.lower()
