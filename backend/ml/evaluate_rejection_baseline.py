"""Phase 3.2: Baseline Evaluation of Pest Classifier on Labeled Pest, Healthy, Disease, and Non-Plant Inputs.

Evaluates the existing closed-set IP102 MobileNetV3-Small classifier and
PlantHealthService.analyze_pests pipeline against:
1. Known Pest Images (IP102 held-out test split, N=1,020)
2. Healthy Foliage Images (PlantVillage Tomato, Pepper, Potato healthy, N=300)
3. Plant Disease Images (PlantVillage Bacterial spot, Early blight, Late blight, Leaf mold, Septoria, Target spot, N=350)
4. Non-Plant Images (UI assets, diagrams, icons, textures, blanks, N=50)

Measures:
- Max softmax score distributions
- Service status distribution (classified_candidate, unsupported_class, inconclusive)
- False candidate rate on non-pest inputs
- Most commonly misclassified pest categories
"""

import os
import sys
import json
import random
import numpy as np
import torch
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from ml.ip102_inference import get_ip102_engine
from ml.dataset_ip102 import IP102Dataset
from services.plant_health_service import PlantHealthService

def evaluate_group(name, images_with_labels, engine):
    """Evaluates a list of (image_path_or_PIL, ground_truth_label) tuples."""
    scores = []
    statuses = {"classified_candidate": 0, "unsupported_class": 0, "inconclusive": 0, "other": 0}
    predicted_classes = {}
    service_statuses = {"classified_candidate": 0, "unsupported_class": 0, "inconclusive": 0}

    for item in images_with_labels:
        if isinstance(item, tuple):
            src, gt_label = item
            if isinstance(src, str):
                try:
                    img = Image.open(src).convert("RGB")
                except Exception as e:
                    continue
            else:
                img = src
        else:
            img = item
            gt_label = "unknown"

        # Engine level prediction
        res = engine.predict(img)
        score = res["raw_softmax_score"]
        status = res["status"]
        p_name = res["raw_class_name"]

        scores.append(score)
        statuses[status] = statuses.get(status, 0) + 1
        predicted_classes[p_name] = predicted_classes.get(p_name, 0) + 1

        # Service level diagnosis
        diag = PlantHealthService.analyze_pests(img)
        service_statuses[diag.status] = service_statuses.get(diag.status, 0) + 1

    scores_arr = np.array(scores) if scores else np.array([0.0])
    
    # Sort top predicted classes
    top_preds = sorted(predicted_classes.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "group_name": name,
        "sample_count": len(scores),
        "mean_score": round(float(np.mean(scores_arr)), 4),
        "median_score": round(float(np.median(scores_arr)), 4),
        "min_score": round(float(np.min(scores_arr)), 4),
        "max_score": round(float(np.max(scores_arr)), 4),
        "std_score": round(float(np.std(scores_arr)), 4),
        "engine_statuses": statuses,
        "service_statuses": service_statuses,
        "above_threshold_count": int(np.sum(scores_arr >= 0.25)),
        "above_threshold_pct": round(float(np.sum(scores_arr >= 0.25) / len(scores_arr) * 100), 2) if len(scores_arr) > 0 else 0.0,
        "top_predicted_classes": top_preds
    }

def collect_healthy_images(pv_root, samples_per_class=100, seed=42):
    random.seed(seed)
    healthy_dirs = [
        ("Tomato_healthy", os.path.join(pv_root, "Tomato_healthy")),
        ("Pepper__bell___healthy", os.path.join(pv_root, "Pepper__bell___healthy")),
        ("Potato___healthy", os.path.join(pv_root, "Potato___healthy"))
    ]
    items = []
    for label, dpath in healthy_dirs:
        if os.path.exists(dpath):
            files = [f for f in os.listdir(dpath) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            chosen = random.sample(files, min(samples_per_class, len(files)))
            for f in chosen:
                items.append((os.path.join(dpath, f), f"Healthy ({label})"))
    return items

def collect_disease_images(pv_root, samples_per_class=50, seed=42):
    random.seed(seed)
    disease_dirs = [
        ("Tomato_Bacterial_spot", os.path.join(pv_root, "Tomato_Bacterial_spot")),
        ("Tomato_Early_blight", os.path.join(pv_root, "Tomato_Early_blight")),
        ("Tomato_Late_blight", os.path.join(pv_root, "Tomato_Late_blight")),
        ("Tomato_Leaf_Mold", os.path.join(pv_root, "Tomato_Leaf_Mold")),
        ("Tomato_Septoria_leaf_spot", os.path.join(pv_root, "Tomato_Septoria_leaf_spot")),
        ("Tomato__Target_Spot", os.path.join(pv_root, "Tomato__Target_Spot")),
        ("Pepper__bell___Bacterial_spot", os.path.join(pv_root, "Pepper__bell___Bacterial_spot")),
    ]
    items = []
    for label, dpath in disease_dirs:
        if os.path.exists(dpath):
            files = [f for f in os.listdir(dpath) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            chosen = random.sample(files, min(samples_per_class, len(files)))
            for f in chosen:
                items.append((os.path.join(dpath, f), f"Disease ({label})"))
    return items

def collect_non_plant_images():
    items = []
    # UI images
    ui_paths = [
        os.path.join(REPO_ROOT, "frontend", "src", "app", "icon.png"),
    ]
    for p in ui_paths:
        if os.path.exists(p):
            items.append((p, "UI Icon"))

    # Synthetic non-plant patterns (soil textures, solid colors, random noise, gradients)
    rng = np.random.RandomState(42)
    # 10 solid colors
    for color in [(0, 0, 0), (255, 255, 255), (128, 128, 128), (139, 69, 19), (210, 180, 140), (70, 130, 180), (255, 0, 0), (0, 0, 255), (255, 255, 0), (200, 200, 200)]:
        arr = np.full((224, 224, 3), color, dtype=np.uint8)
        items.append((Image.fromarray(arr), "Solid Color Pattern"))

    # 15 random noise / textures
    for _ in range(15):
        arr = rng.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        items.append((Image.fromarray(arr), "Random Synthetic Noise"))

    # 15 soil-like brown/black noise patterns
    for _ in range(15):
        base = np.array([80, 50, 30], dtype=np.float32)
        noise = rng.normal(0, 20, (224, 224, 3))
        arr = np.clip(base + noise, 0, 255).astype(np.uint8)
        items.append((Image.fromarray(arr), "Potting Mix / Soil Texture Simulation"))

    # 10 geometric gradients
    for _ in range(10):
        grad = np.tile(np.linspace(0, 255, 224, dtype=np.uint8), (224, 1))
        arr = np.stack([grad, grad[::-1], grad], axis=-1)
        items.append((Image.fromarray(arr), "Geometric Gradient Pattern"))

    return items

def main():
    print("=== Running Phase 3.2 Pest Presence & Rejection Baseline Evaluation ===")
    engine = get_ip102_engine()
    engine.load_artifacts()

    # 1. Known Pest Images: IP102 Test Split
    print("\n--- 1. Evaluating Known Pest Images (IP102 Test Split, N=1,020) ---")
    dataset_root = os.path.join(REPO_ROOT, "datasets", "pests")
    test_ds = IP102Dataset(dataset_root=dataset_root, split="test", max_samples_per_class=10, random_seed=42)
    pest_items = [(path, f"IP102 Class {c}") for path, c in test_ds.samples]
    pest_results = evaluate_group("Known Pest Images (IP102 Test)", pest_items, engine)

    # 2. Healthy Foliage Images: PlantVillage
    print("\n--- 2. Evaluating Healthy Foliage Images (PlantVillage, N=300) ---")
    pv_root = os.path.join(REPO_ROOT, "datasets", "plant_diseases", "PlantVillage")
    healthy_items = collect_healthy_images(pv_root, samples_per_class=100)
    healthy_results = evaluate_group("Healthy Foliage (PlantVillage)", healthy_items, engine)

    # 3. Plant Disease Images: PlantVillage (Bacterial spot, Early/Late blight, etc.)
    print("\n--- 3. Evaluating Plant Disease Images (PlantVillage, N=350) ---")
    disease_items = collect_disease_images(pv_root, samples_per_class=50)
    disease_results = evaluate_group("Plant Disease Images (PlantVillage)", disease_items, engine)

    # 4. Non-Plant Images
    print("\n--- 4. Evaluating Non-Plant Images (UI & Synthetic Textures, N=51) ---")
    non_plant_items = collect_non_plant_images()
    non_plant_results = evaluate_group("Non-Plant Images", non_plant_items, engine)

    all_results = {
        "known_pests": pest_results,
        "healthy_foliage": healthy_results,
        "plant_disease": disease_results,
        "non_plant": non_plant_results
    }

    out_path = os.path.join(BACKEND_DIR, "ml", "artifacts", "rejection_baseline_evaluation.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nSaved evaluation results to {out_path}")
    print("\nSummary Results:")
    for key, res in all_results.items():
        print(f"\n[{res['group_name']}] (N={res['sample_count']})")
        print(f"  Mean Softmax Score: {res['mean_score']} (Median: {res['median_score']}, Std: {res['std_score']})")
        print(f"  Above 25% Threshold: {res['above_threshold_count']}/{res['sample_count']} ({res['above_threshold_pct']}%)")
        print(f"  Service Statuses: {res['service_statuses']}")
        print(f"  Top 3 Triggered Classes: {res['top_predicted_classes'][:3]}")

if __name__ == "__main__":
    main()
