"""Phase 3.3 Controlled Experiment: Pest Presence Screening, False-Positive Reduction, and Classification Reliability.

Rigorous, isolated evaluation harness comparing:
- Baseline (A0): Verified production baseline (tau = 0.25 uniform)
- Experiment A1: Tiered thresholds (tau_validated = 0.25, tau_candidate = 0.35)
- Experiment A2: Tiered thresholds (tau_validated = 0.25, tau_candidate = 0.40)
- Experiment B: Disease-model-assisted rejection (evaluating tau_disease = 0.60, 0.70, 0.75, 0.80)
- Experiment C: Combined tiered thresholds + disease-assisted rejection

Evaluates:
- Genuine Pests (IP102 Test Split, N=1,020, 10 per class across 102 classes)
- Healthy Foliage (PlantVillage Tomato, Pepper, Potato healthy, N=300)
- Plant Disease Foliage (PlantVillage Bacterial spot, Blights, Leaf mold, Septoria, Target spot, N=350)
- Non-Plant Controls (UI assets, soil textures, gradients, noise, N=51)
Total: 1,721 samples.

Preserves production code strictly without modification.
"""

import os
import sys
import time
import json
import csv
import random
import math
import numpy as np
import torch
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from ml.ip102_inference import get_ip102_engine, IP102InferenceEngine
from ml.plant_disease_dl import PlantDiseaseDeepLearningEngine
from ml.dataset_ip102 import IP102Dataset

EXPERIMENT_DIR = os.path.abspath(os.path.dirname(__file__))

def wilson_score_interval(k, n, confidence=0.95):
    """Computes Wilson score interval for binomial proportion."""
    if n == 0:
        return 0.0, 0.0, 0.0
    z = 1.95996  # 95% confidence
    p = k / n
    denominator = 1 + z**2 / n
    centre_adjusted_probability = p + z**2 / (2 * n)
    adjusted_std_dev = math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n)
    lower = max(0.0, (centre_adjusted_probability - z * adjusted_std_dev) / denominator)
    upper = min(1.0, (centre_adjusted_probability + z * adjusted_std_dev) / denominator)
    return round(p, 4), round(lower, 4), round(upper, 4)

def collect_evaluation_samples(seed=42):
    """Collects exactly 1,721 evaluation samples matching Phase 3.2 baseline."""
    random.seed(seed)
    samples = []

    # 1. IP102 Test Split (10 per class, 102 classes = 1,020 samples)
    dataset_root = os.path.join(REPO_ROOT, "datasets", "pests")
    test_ds = IP102Dataset(dataset_root=dataset_root, split="test", max_samples_per_class=10, random_seed=seed)
    for idx, (path, c_idx) in enumerate(test_ds.samples):
        samples.append({
            "sample_id": f"pest_{idx:04d}",
            "source_path": path,
            "image_obj": None,
            "domain": "genuine_pest",
            "ground_truth_label": test_ds.class_names[c_idx],
            "ground_truth_idx": c_idx,
            "plant_host": "agricultural_field_crop"
        })

    # 2. PlantVillage Healthy Foliage (N=300: 100 Tomato, 100 Pepper, 100 Potato)
    pv_root = os.path.join(REPO_ROOT, "datasets", "plant_diseases", "PlantVillage")
    healthy_cfgs = [
        ("Tomato", "Tomato_healthy", 100),
        ("Pepper", "Pepper__bell___healthy", 100),
        ("Potato", "Potato___healthy", 100)
    ]
    h_idx = 0
    for host, label, count in healthy_cfgs:
        dpath = os.path.join(pv_root, label)
        if os.path.exists(dpath):
            files = sorted([f for f in os.listdir(dpath) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            chosen = random.sample(files, min(count, len(files)))
            for f in chosen:
                samples.append({
                    "sample_id": f"healthy_{h_idx:04d}",
                    "source_path": os.path.join(dpath, f),
                    "image_obj": None,
                    "domain": "healthy_foliage",
                    "ground_truth_label": f"Healthy_{host}",
                    "ground_truth_idx": -1,
                    "plant_host": host.lower()
                })
                h_idx += 1

    # 3. PlantVillage Disease Foliage (N=350: 7 classes x 50 samples)
    disease_cfgs = [
        ("Tomato", "Tomato_Bacterial_spot", 50),
        ("Tomato", "Tomato_Early_blight", 50),
        ("Tomato", "Tomato_Late_blight", 50),
        ("Tomato", "Tomato_Leaf_Mold", 50),
        ("Tomato", "Tomato_Septoria_leaf_spot", 50),
        ("Tomato", "Tomato__Target_Spot", 50),
        ("Pepper", "Pepper__bell___Bacterial_spot", 50)
    ]
    d_idx = 0
    for host, label, count in disease_cfgs:
        dpath = os.path.join(pv_root, label)
        if os.path.exists(dpath):
            files = sorted([f for f in os.listdir(dpath) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            chosen = random.sample(files, min(count, len(files)))
            for f in chosen:
                samples.append({
                    "sample_id": f"disease_{d_idx:04d}",
                    "source_path": os.path.join(dpath, f),
                    "image_obj": None,
                    "domain": "plant_disease",
                    "ground_truth_label": label,
                    "ground_truth_idx": -2,
                    "plant_host": host.lower()
                })
                d_idx += 1

    # 4. Non-Plant Controls (N=51: UI icon + synthetic controls)
    np_idx = 0
    ui_path = os.path.join(REPO_ROOT, "frontend", "src", "app", "icon.png")
    if os.path.exists(ui_path):
        samples.append({
            "sample_id": f"non_plant_{np_idx:04d}",
            "source_path": ui_path,
            "image_obj": None,
            "domain": "non_plant",
            "ground_truth_label": "UI_App_Icon",
            "ground_truth_idx": -3,
            "plant_host": "none"
        })
        np_idx += 1

    rng = np.random.RandomState(42)
    # 10 solid colors
    for color in [(0, 0, 0), (255, 255, 255), (128, 128, 128), (139, 69, 19), (210, 180, 140), (70, 130, 180), (255, 0, 0), (0, 0, 255), (255, 255, 0), (200, 200, 200)]:
        arr = np.full((224, 224, 3), color, dtype=np.uint8)
        samples.append({
            "sample_id": f"non_plant_{np_idx:04d}",
            "source_path": None,
            "image_obj": Image.fromarray(arr),
            "domain": "non_plant",
            "ground_truth_label": "Solid_Color_Control",
            "ground_truth_idx": -3,
            "plant_host": "none"
        })
        np_idx += 1

    # 15 random noise
    for _ in range(15):
        arr = rng.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        samples.append({
            "sample_id": f"non_plant_{np_idx:04d}",
            "source_path": None,
            "image_obj": Image.fromarray(arr),
            "domain": "non_plant",
            "ground_truth_label": "Random_Noise_Control",
            "ground_truth_idx": -3,
            "plant_host": "none"
        })
        np_idx += 1

    # 15 soil textures
    for _ in range(15):
        base = np.array([80, 50, 30], dtype=np.float32)
        noise = rng.normal(0, 20, (224, 224, 3))
        arr = np.clip(base + noise, 0, 255).astype(np.uint8)
        samples.append({
            "sample_id": f"non_plant_{np_idx:04d}",
            "source_path": None,
            "image_obj": Image.fromarray(arr),
            "domain": "non_plant",
            "ground_truth_label": "Soil_Texture_Control",
            "ground_truth_idx": -3,
            "plant_host": "none"
        })
        np_idx += 1

    # 10 geometric gradients
    for _ in range(10):
        grad = np.tile(np.linspace(0, 255, 224, dtype=np.uint8), (224, 1))
        arr = np.stack([grad, grad[::-1], grad], axis=-1)
        samples.append({
            "sample_id": f"non_plant_{np_idx:04d}",
            "source_path": None,
            "image_obj": Image.fromarray(arr),
            "domain": "non_plant",
            "ground_truth_label": "Geometric_Gradient_Control",
            "ground_truth_idx": -3,
            "plant_host": "none"
        })
        np_idx += 1

    return samples

def compute_model_outputs(samples, pest_engine, disease_engine):
    """Runs a single forward pass per model per sample and caches raw predictions."""
    print(f"Caching forward passes for {len(samples)} samples...")
    raw_results = []
    
    for idx, s in enumerate(samples):
        if idx % 200 == 0:
            print(f"  Processed {idx}/{len(samples)} samples...")
        
        # Load image
        if s["image_obj"] is not None:
            img = s["image_obj"]
        else:
            try:
                img = Image.open(s["source_path"]).convert("RGB")
            except Exception as e:
                img = Image.new("RGB", (224, 224), (0, 0, 0))

        # 1. IP102 Inference (raw forward pass)
        tensor = pest_engine.transforms(img).unsqueeze(0).to(pest_engine.device)
        with torch.no_grad():
            logits = pest_engine.model(tensor)
            probs = torch.softmax(logits, dim=1)[0]
            top_scores, top_indices = torch.topk(probs, 5)

        top_indices = top_indices.cpu().tolist()
        top_scores = [float(x) for x in top_scores.cpu().tolist()]

        p_idx = top_indices[0]
        p_score = top_scores[0]
        p_name = pest_engine.id_to_name.get(p_idx, f"Class {p_idx}")
        p_mapping = pest_engine.terrace_mappings.get(p_idx, {})
        p_taxonomy = p_mapping.get("status", "unsupported")
        p_family = p_mapping.get("target_pest_family")

        is_top1_correct = (s["ground_truth_idx"] == p_idx) if s["domain"] == "genuine_pest" else False
        is_top5_correct = (s["ground_truth_idx"] in top_indices) if s["domain"] == "genuine_pest" else False

        # 2. Plant Disease Inference (raw forward pass)
        dis_preds = disease_engine.predict(img)
        # dis_preds is a list of dicts: [{'class_raw': ..., 'probability': ...}, ...]
        top_dis = dis_preds[0] if dis_preds else {"class_raw": "None", "probability": 0.0}
        dis_name = top_dis["class_raw"]
        dis_prob = float(top_dis["probability"])

        # Determine if top disease class represents an actual foliar pathology (not healthy, not mite)
        is_solanaceae_disease = False
        if any(term in dis_name for term in ["Bacterial_spot", "Early_blight", "Late_blight", "Leaf_Mold", "Septoria", "Target_Spot", "mosaic_virus", "YellowLeaf"]):
            is_solanaceae_disease = True

        raw_results.append({
            "sample_id": s["sample_id"],
            "domain": s["domain"],
            "ground_truth_label": s["ground_truth_label"],
            "ground_truth_idx": s["ground_truth_idx"],
            "plant_host": s["plant_host"],
            "ip102_top1_idx": p_idx,
            "ip102_top1_name": p_name,
            "ip102_top1_score": round(p_score, 4),
            "ip102_top5_indices": top_indices,
            "ip102_top5_scores": [round(x, 4) for x in top_scores],
            "ip102_taxonomy_status": p_taxonomy,
            "ip102_terrace_family": p_family,
            "is_ip102_top1_correct": is_top1_correct,
            "is_ip102_top5_correct": is_top5_correct,
            "disease_top1_name": dis_name,
            "disease_top1_prob": round(dis_prob, 4),
            "disease_is_solanaceae_pathology": is_solanaceae_disease
        })

    print(f"Completed caching for {len(raw_results)} samples.")
    return raw_results

def apply_classification_rules(item, strategy_name, tau_val=0.25, tau_cand=0.25, tau_unsup=0.25, disease_gating=False, tau_dis=0.75, tau_suppress_pest=0.45):
    """Determines decision status under given experimental strategy."""
    score = item["ip102_top1_score"]
    tax_status = item["ip102_taxonomy_status"]

    # 1. Determine active threshold based on taxonomy category
    if tax_status == "validated":
        threshold = tau_val
    elif tax_status == "candidate":
        threshold = tau_cand
    else:  # unsupported
        threshold = tau_unsup

    # 2. Check threshold acceptance
    if score < threshold:
        decision_status = "inconclusive"
    elif tax_status == "unsupported":
        decision_status = "unsupported_class"
    else:
        decision_status = "classified_candidate"

    # 3. Disease-assisted rejection gating (if enabled)
    disease_suppression_applied = False
    if disease_gating and decision_status in ["classified_candidate", "unsupported_class"]:
        # Only Solanaceae hosts (or domain disease/healthy from Solanaceae)
        # If disease model predicts a verified Solanaceae foliar disease with high confidence
        # and pest candidate score is below suppression ceiling:
        if item["disease_is_solanaceae_pathology"] and item["disease_top1_prob"] >= tau_dis and score < tau_suppress_pest:
            # Suppress pest candidate to inconclusive (identified as foliar pathology)
            decision_status = "inconclusive"
            disease_suppression_applied = True

    return decision_status, disease_suppression_applied

def evaluate_configuration(raw_results, config_name, **rules):
    """Evaluates all Section 4 metrics for a specific experimental strategy."""
    # Group buckets
    pests = [r for r in raw_results if r["domain"] == "genuine_pest"]
    healthy = [r for r in raw_results if r["domain"] == "healthy_foliage"]
    disease = [r for r in raw_results if r["domain"] == "plant_disease"]
    non_plant = [r for r in raw_results if r["domain"] == "non_plant"]

    def run_strategy_on_group(items):
        decisions = []
        suppressions = 0
        for it in items:
            st, supp = apply_classification_rules(it, config_name, **rules)
            decisions.append((st, it))
            if supp:
                suppressions += 1
        return decisions, suppressions

    pest_decisions, pest_supp = run_strategy_on_group(pests)
    healthy_decisions, _ = run_strategy_on_group(healthy)
    disease_decisions, dis_supp = run_strategy_on_group(disease)
    non_plant_decisions, _ = run_strategy_on_group(non_plant)

    # ── Metric A: Pest Acceptance Recall ──
    # Total accepted (candidate + unsupported)
    pest_accepted_total = sum(1 for st, _ in pest_decisions if st in ["classified_candidate", "unsupported_class"])
    pest_accepted_candidate = sum(1 for st, _ in pest_decisions if st == "classified_candidate")
    pest_accepted_unsupported = sum(1 for st, _ in pest_decisions if st == "unsupported_class")
    pest_inconclusive = sum(1 for st, _ in pest_decisions if st == "inconclusive")

    p_rec_tot, p_rec_tot_lo, p_rec_tot_hi = wilson_score_interval(pest_accepted_total, len(pests))
    p_rec_cand, p_rec_cand_lo, p_rec_cand_hi = wilson_score_interval(pest_accepted_candidate, len(pests))

    # ── Metric B: False-Positive Rates ──
    fp_healthy = sum(1 for st, _ in healthy_decisions if st == "classified_candidate")
    fpr_h, fpr_h_lo, fpr_h_hi = wilson_score_interval(fp_healthy, len(healthy))

    fp_disease = sum(1 for st, _ in disease_decisions if st in ["classified_candidate", "unsupported_class"])
    fp_disease_candidate = sum(1 for st, _ in disease_decisions if st == "classified_candidate")
    fpr_d, fpr_d_lo, fpr_d_hi = wilson_score_interval(fp_disease, len(disease))

    fp_non_plant = sum(1 for st, _ in non_plant_decisions if st in ["classified_candidate", "unsupported_class"])
    fpr_np, fpr_np_lo, fpr_np_hi = wilson_score_interval(fp_non_plant, len(non_plant))

    total_negatives = len(healthy) + len(disease) + len(non_plant)
    total_fp = fp_healthy + fp_disease + fp_non_plant
    fpr_overall, fpr_ov_lo, fpr_ov_hi = wilson_score_interval(total_fp, total_negatives)

    # ── Metric C: Pest-Presence Precision ──
    # Definition 1: All accepted predictions (including unsupported agricultural classes)
    # Denominator: pest_accepted_total + total_fp
    den_def1 = pest_accepted_total + total_fp
    prec_def1, prec_d1_lo, prec_d1_hi = wilson_score_interval(pest_accepted_total, den_def1) if den_def1 > 0 else (0.0, 0.0, 0.0)

    # Definition 2: Strictly supported terrace candidate predictions (classified_candidate only)
    # Denominator: pest_accepted_candidate + fp_healthy + fp_disease_candidate + fp_non_plant
    total_fp_cand = fp_healthy + fp_disease_candidate + fp_non_plant
    den_def2 = pest_accepted_candidate + total_fp_cand
    prec_def2, prec_d2_lo, prec_d2_hi = wilson_score_interval(pest_accepted_candidate, den_def2) if den_def2 > 0 else (0.0, 0.0, 0.0)

    # ── Metric D: Supported-Class Coverage (among genuine pests, N=1,020) ──
    cov_val = sum(1 for st, it in pest_decisions if st == "classified_candidate" and it["ip102_taxonomy_status"] == "validated")
    cov_cand = sum(1 for st, it in pest_decisions if st == "classified_candidate" and it["ip102_taxonomy_status"] == "candidate")
    cov_unsup = sum(1 for st, it in pest_decisions if st == "unsupported_class")

    # ── Metric E & F: Species-Level Accuracy ──
    # Top-1 accuracy across all 1,020 genuine pests (whether accepted or not)
    correct_top1_all = sum(1 for _, it in pest_decisions if it["is_ip102_top1_correct"])
    acc_top1_all, _, _ = wilson_score_interval(correct_top1_all, len(pests))

    correct_top5_all = sum(1 for _, it in pest_decisions if it["is_ip102_top5_correct"])
    acc_top5_all, _, _ = wilson_score_interval(correct_top5_all, len(pests))

    # Metric F: Species Correctness among accepted predictions
    correct_top1_accepted = sum(1 for st, it in pest_decisions if st in ["classified_candidate", "unsupported_class"] and it["is_ip102_top1_correct"])
    spec_prec_accepted, spec_prec_lo, spec_prec_hi = wilson_score_interval(correct_top1_accepted, pest_accepted_total) if pest_accepted_total > 0 else (0.0, 0.0, 0.0)

    # Macro-F1 across 102 classes on accepted predictions
    class_tp = {c: 0 for c in range(102)}
    class_fp = {c: 0 for c in range(102)}
    class_fn = {c: 0 for c in range(102)}
    for st, it in pest_decisions:
        gt = it["ground_truth_idx"]
        pred = it["ip102_top1_idx"]
        if st in ["classified_candidate", "unsupported_class"]:
            if pred == gt:
                class_tp[gt] += 1
            else:
                class_fp[pred] += 1
                class_fn[gt] += 1
        else:
            class_fn[gt] += 1

    f1s = []
    for c in range(102):
        tp_c = class_tp[c]
        fp_c = class_fp[c]
        fn_c = class_fn[c]
        p_c = tp_c / (tp_c + fp_c) if (tp_c + fp_c) > 0 else 0.0
        r_c = tp_c / (tp_c + fn_c) if (tp_c + fn_c) > 0 else 0.0
        f1_c = (2 * p_c * r_c) / (p_c + r_c) if (p_c + r_c) > 0 else 0.0
        f1s.append(f1_c)
    macro_f1 = round(float(np.mean(f1s)), 4)

    # ── Metric G: Abstention & Inconclusive Rates ──
    abstention_pest = pest_inconclusive / len(pests)
    abstention_healthy = sum(1 for st, _ in healthy_decisions if st == "inconclusive") / len(healthy)
    abstention_disease = sum(1 for st, _ in disease_decisions if st == "inconclusive") / len(disease)
    abstention_non_plant = sum(1 for st, _ in non_plant_decisions if st == "inconclusive") / len(non_plant)

    # Binary Confusion Matrix counts
    tp = pest_accepted_total
    fn = pest_inconclusive
    fp = total_fp
    tn = total_negatives - total_fp

    return {
        "configuration": config_name,
        "rules": rules,
        "sample_counts": {
            "genuine_pests": len(pests),
            "healthy_foliage": len(healthy),
            "plant_disease": len(disease),
            "non_plant": len(non_plant),
            "total_samples": len(raw_results)
        },
        "metric_a_acceptance_recall": {
            "total_accepted_pests": pest_accepted_total,
            "total_accepted_recall": p_rec_tot,
            "total_accepted_recall_ci95": [p_rec_tot_lo, p_rec_tot_hi],
            "candidate_accepted_pests": pest_accepted_candidate,
            "candidate_accepted_recall": p_rec_cand,
            "candidate_accepted_recall_ci95": [p_rec_cand_lo, p_rec_cand_hi],
            "unsupported_accepted_pests": pest_accepted_unsupported
        },
        "metric_b_false_positive_rates": {
            "healthy_fp": fp_healthy,
            "healthy_total": len(healthy),
            "healthy_fpr": fpr_h,
            "healthy_fpr_ci95": [fpr_h_lo, fpr_h_hi],
            "disease_fp": fp_disease,
            "disease_total": len(disease),
            "disease_fpr": fpr_d,
            "disease_fpr_ci95": [fpr_d_lo, fpr_d_hi],
            "non_plant_fp": fp_non_plant,
            "non_plant_total": len(non_plant),
            "non_plant_fpr": fpr_np,
            "overall_fp": total_fp,
            "overall_negatives": total_negatives,
            "overall_fpr": fpr_overall,
            "overall_fpr_ci95": [fpr_ov_lo, fpr_ov_hi]
        },
        "metric_c_pest_presence_precision": {
            "def1_all_accepted_precision": prec_def1,
            "def1_all_accepted_ci95": [prec_d1_lo, prec_d1_hi],
            "def1_numerator_pests": pest_accepted_total,
            "def1_denominator_total": den_def1,
            "def2_candidate_only_precision": prec_def2,
            "def2_candidate_only_ci95": [prec_d2_lo, prec_d2_hi],
            "def2_numerator_candidates": pest_accepted_candidate,
            "def2_denominator_total": den_def2
        },
        "metric_d_supported_coverage": {
            "validated_count": cov_val,
            "validated_pct": round(cov_val / len(pests) * 100, 2),
            "candidate_count": cov_cand,
            "candidate_pct": round(cov_cand / len(pests) * 100, 2),
            "unsupported_count": cov_unsup,
            "unsupported_pct": round(cov_unsup / len(pests) * 100, 2)
        },
        "metric_e_species_level_accuracy": {
            "top1_overall_correct": correct_top1_all,
            "top1_overall_accuracy": acc_top1_all,
            "top5_overall_correct": correct_top5_all,
            "top5_overall_accuracy": acc_top5_all,
            "macro_f1_score": macro_f1
        },
        "metric_f_accepted_species_correctness": {
            "correct_and_accepted": correct_top1_accepted,
            "accepted_total": pest_accepted_total,
            "species_accuracy_among_accepted": spec_prec_accepted,
            "species_accuracy_ci95": [spec_prec_lo, spec_prec_hi]
        },
        "metric_g_abstention_rates": {
            "pest_inconclusive_count": pest_inconclusive,
            "pest_inconclusive_rate": round(abstention_pest, 4),
            "healthy_inconclusive_rate": round(abstention_healthy, 4),
            "disease_inconclusive_rate": round(abstention_disease, 4),
            "non_plant_inconclusive_rate": round(abstention_non_plant, 4)
        },
        "disease_suppression_telemetry": {
            "genuine_pests_suppressed": pest_supp,
            "disease_false_positives_suppressed": dis_supp
        },
        "binary_confusion_matrix": {
            "TP": tp,
            "FN": fn,
            "FP": fp,
            "TN": tn
        }
    }

def measure_runtime_latency(pest_engine, disease_engine, img_size=(224, 224), n_runs=100, n_warmup=20):
    """Measures median and p95 CPU execution latency for single and dual model inference."""
    dummy_img = Image.new("RGB", img_size, (100, 150, 80))
    
    # Warmup
    for _ in range(n_warmup):
        _ = pest_engine.predict(dummy_img)
        _ = disease_engine.predict(dummy_img)

    # 1. IP102 only
    ip102_times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        _ = pest_engine.predict(dummy_img)
        t1 = time.perf_counter()
        ip102_times.append((t1 - t0) * 1000.0)

    # 2. Disease only
    dis_times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        _ = disease_engine.predict(dummy_img)
        t1 = time.perf_counter()
        dis_times.append((t1 - t0) * 1000.0)

    # 3. Dual model pipeline
    dual_times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        _ = pest_engine.predict(dummy_img)
        _ = disease_engine.predict(dummy_img)
        t1 = time.perf_counter()
        dual_times.append((t1 - t0) * 1000.0)

    return {
        "runs": n_runs,
        "warmup": n_warmup,
        "ip102_only_ms": {
            "median": round(float(np.median(ip102_times)), 2),
            "mean": round(float(np.mean(ip102_times)), 2),
            "p95": round(float(np.percentile(ip102_times, 95)), 2),
            "std": round(float(np.std(ip102_times)), 2)
        },
        "disease_only_ms": {
            "median": round(float(np.median(dis_times)), 2),
            "mean": round(float(np.mean(dis_times)), 2),
            "p95": round(float(np.percentile(dis_times, 95)), 2),
            "std": round(float(np.std(dis_times)), 2)
        },
        "dual_pipeline_ms": {
            "median": round(float(np.median(dual_times)), 2),
            "mean": round(float(np.mean(dual_times)), 2),
            "p95": round(float(np.percentile(dual_times, 95)), 2),
            "std": round(float(np.std(dual_times)), 2)
        }
    }

def main():
    print("=" * 70)
    print("PHASE 3.3 CONTROLLED EXPERIMENT: PEST PRESENCE & RELIABILITY")
    print("=" * 70)

    os.makedirs(EXPERIMENT_DIR, exist_ok=True)

    pest_engine = get_ip102_engine()
    pest_engine.load_artifacts()

    disease_engine = PlantDiseaseDeepLearningEngine()

    # 1. Collect exact 1,721 evaluation samples
    samples = collect_evaluation_samples(seed=42)
    print(f"Total evaluation samples collected: {len(samples)}")
    print(f"  Pests: {sum(1 for s in samples if s['domain']=='genuine_pest')}")
    print(f"  Healthy: {sum(1 for s in samples if s['domain']=='healthy_foliage')}")
    print(f"  Disease: {sum(1 for s in samples if s['domain']=='plant_disease')}")
    print(f"  Non-Plant: {sum(1 for s in samples if s['domain']=='non_plant')}")

    # 2. Compute and cache model forward passes
    raw_results = compute_model_outputs(samples, pest_engine, disease_engine)

    # 3. Define and evaluate experimental configurations
    configs = [
        # Baseline A0: Verified Production Baseline
        ("Baseline (A0)", {"tau_val": 0.25, "tau_cand": 0.25, "tau_unsup": 0.25, "disease_gating": False}),
        
        # Experiment A: Tiered Thresholds Only
        ("Tiered Thresholds (A1: 0.25/0.35)", {"tau_val": 0.25, "tau_cand": 0.35, "tau_unsup": 0.25, "disease_gating": False}),
        ("Tiered Thresholds (A2: 0.25/0.40)", {"tau_val": 0.25, "tau_cand": 0.40, "tau_unsup": 0.25, "disease_gating": False}),
        
        # Experiment B: Disease-Assisted Rejection Only (tau_disease = 0.75, tau_suppress_pest = 0.45)
        ("Disease-Assisted Rejection (B: tau_dis=0.75)", {"tau_val": 0.25, "tau_cand": 0.25, "tau_unsup": 0.25, "disease_gating": True, "tau_dis": 0.75, "tau_suppress_pest": 0.45}),
        ("Disease-Assisted Rejection (B: tau_dis=0.60)", {"tau_val": 0.25, "tau_cand": 0.25, "tau_unsup": 0.25, "disease_gating": True, "tau_dis": 0.60, "tau_suppress_pest": 0.45}),
        
        # Experiment C: Combined Tiered Thresholds + Disease Rejection
        ("Combined Strategy (C1: A1 + B_0.75)", {"tau_val": 0.25, "tau_cand": 0.35, "tau_unsup": 0.25, "disease_gating": True, "tau_dis": 0.75, "tau_suppress_pest": 0.45}),
        ("Combined Strategy (C2: A2 + B_0.75)", {"tau_val": 0.25, "tau_cand": 0.40, "tau_unsup": 0.25, "disease_gating": True, "tau_dis": 0.75, "tau_suppress_pest": 0.45}),
    ]

    all_config_results = {}
    for name, params in configs:
        print(f"\nEvaluating Configuration: {name}...")
        res = evaluate_configuration(raw_results, name, **params)
        all_config_results[name] = res
        print(f"  Pest Acceptance Recall: {res['metric_a_acceptance_recall']['total_accepted_recall']*100:.2f}% (Pests accepted: {res['metric_a_acceptance_recall']['total_accepted_pests']})")
        print(f"  False-Positive Rate - Healthy: {res['metric_b_false_positive_rates']['healthy_fpr']*100:.2f}% ({res['metric_b_false_positive_rates']['healthy_fp']}/300)")
        print(f"  False-Positive Rate - Disease: {res['metric_b_false_positive_rates']['disease_fpr']*100:.2f}% ({res['metric_b_false_positive_rates']['disease_fp']}/350)")
        print(f"  Overall False-Positive Rate: {res['metric_b_false_positive_rates']['overall_fpr']*100:.2f}% ({res['metric_b_false_positive_rates']['overall_fp']}/701)")
        print(f"  Pest-Presence Precision (Def 1 All Accepted): {res['metric_c_pest_presence_precision']['def1_all_accepted_precision']*100:.2f}%")
        print(f"  Pest-Presence Precision (Def 2 Candidate Only): {res['metric_c_pest_presence_precision']['def2_candidate_only_precision']*100:.2f}%")
        print(f"  Species Correctness among Accepted: {res['metric_f_accepted_species_correctness']['species_accuracy_among_accepted']*100:.2f}%")
        if params.get("disease_gating"):
            print(f"  Disease Telemetry: Genuine Pests Suppressed: {res['disease_suppression_telemetry']['genuine_pests_suppressed']}, Disease FPs Suppressed: {res['disease_suppression_telemetry']['disease_false_positives_suppressed']}")

    # 4. Measure Runtime Latency
    print("\nMeasuring runtime latency (100 runs on CPU)...")
    latency_report = measure_runtime_latency(pest_engine, disease_engine, n_runs=100, n_warmup=20)
    print(f"  IP102 Only Latency: Median = {latency_report['ip102_only_ms']['median']} ms, p95 = {latency_report['ip102_only_ms']['p95']} ms")
    print(f"  Disease Only Latency: Median = {latency_report['disease_only_ms']['median']} ms, p95 = {latency_report['disease_only_ms']['p95']} ms")
    print(f"  Dual Pipeline Latency: Median = {latency_report['dual_pipeline_ms']['median']} ms, p95 = {latency_report['dual_pipeline_ms']['p95']} ms")

    # 5. Save per-image results CSV
    csv_path = os.path.join(EXPERIMENT_DIR, "phase_3_3_per_image_results.csv")
    print(f"\nWriting per-image evaluation results to {csv_path}...")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "sample_id", "domain", "ground_truth_label", "ground_truth_idx", "plant_host",
            "ip102_top1_idx", "ip102_top1_name", "ip102_top1_score", "ip102_taxonomy_status",
            "is_ip102_top1_correct", "is_ip102_top5_correct",
            "disease_top1_name", "disease_top1_prob", "disease_is_solanaceae_pathology",
            "status_baseline_A0", "status_tiered_A1", "status_tiered_A2",
            "status_disease_B", "status_combined_C1", "status_combined_C2"
        ])
        for it in raw_results:
            st_a0, _ = apply_classification_rules(it, "A0", tau_val=0.25, tau_cand=0.25, tau_unsup=0.25, disease_gating=False)
            st_a1, _ = apply_classification_rules(it, "A1", tau_val=0.25, tau_cand=0.35, tau_unsup=0.25, disease_gating=False)
            st_a2, _ = apply_classification_rules(it, "A2", tau_val=0.25, tau_cand=0.40, tau_unsup=0.25, disease_gating=False)
            st_b, _ = apply_classification_rules(it, "B", tau_val=0.25, tau_cand=0.25, tau_unsup=0.25, disease_gating=True, tau_dis=0.75, tau_suppress_pest=0.45)
            st_c1, _ = apply_classification_rules(it, "C1", tau_val=0.25, tau_cand=0.35, tau_unsup=0.25, disease_gating=True, tau_dis=0.75, tau_suppress_pest=0.45)
            st_c2, _ = apply_classification_rules(it, "C2", tau_val=0.25, tau_cand=0.40, tau_unsup=0.25, disease_gating=True, tau_dis=0.75, tau_suppress_pest=0.45)

            writer.writerow([
                it["sample_id"], it["domain"], it["ground_truth_label"], it["ground_truth_idx"], it["plant_host"],
                it["ip102_top1_idx"], it["ip102_top1_name"], it["ip102_top1_score"], it["ip102_taxonomy_status"],
                it["is_ip102_top1_correct"], it["is_ip102_top5_correct"],
                it["disease_top1_name"], it["disease_top1_prob"], it["disease_is_solanaceae_pathology"],
                st_a0, st_a1, st_a2, st_b, st_c1, st_c2
            ])

    # 6. Save comprehensive machine-readable results JSON
    final_output = {
        "metadata": {
            "title": "Phase 3.3 Controlled Experiment: Pest Presence Screening & Reliability",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "evaluation_samples_total": len(raw_results),
            "ip102_checkpoint": "best_checkpoint.pt",
            "disease_model": "model_scripted.pt",
            "device": "CPU"
        },
        "configurations": all_config_results,
        "runtime_latency": latency_report
    }

    json_path = os.path.join(EXPERIMENT_DIR, "phase_3_3_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    print(f"\nSaved machine-readable results to {json_path}")
    print("=" * 70)
    print("PHASE 3.3 CONTROLLED EXPERIMENT COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    main()
