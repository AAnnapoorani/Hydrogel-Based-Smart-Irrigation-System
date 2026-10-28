"""Phase 3.4 Controlled Experiment: Non-Solanaceae Negative Foliage & Open-Set OOD Screening.

Rigorous, isolated evaluation harness comparing:
- Baseline (C1 from Phase 3.3): Tiered thresholds (0.25 val / 0.35 cand) + Solanaceae disease gating
- Strategy D1: Free Energy OOD Prescreening (-E(x) >= tau_energy)
- Strategy D2: Max Logit Score (MLS) Prescreening (max(z) >= tau_mls)
- Strategy D3: Calibrated Microscopic Pest Gating (Chilli Thrips threshold rebalancing)
- Strategy D4: Multi-Stage Integrated Architecture (Energy OOD + Calibrated Thrips + Tiered Candidate + Disease Gating)

Evaluation Dataset Scope (N = 1,971):
1. IP102 Test Split Genuine Pests (N=1,020, exactly 10 per class across 102 classes)
2. Solanaceae Healthy Foliage (N=300: 100 Tomato, 100 Pepper, 100 Potato)
3. Non-Solanaceae Healthy Foliage (N=250: 50 Strawberry, 50 Soybean, 50 Corn, 50 Grape, 50 Apple)
4. Plant Disease Foliage (N=350: 7 classes x 50 samples)
5. Non-Plant Controls (N=51: UI icon, solid colors, noise, soil textures, gradients)
Total: 1,971 samples.

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

from ml.ip102_inference import get_ip102_engine
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
    """Collects exactly 1,971 evaluation samples across all target domains."""
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
            "botanical_family": "field_crop",
            "ground_truth_label": test_ds.class_names[c_idx],
            "ground_truth_idx": c_idx,
            "plant_host": "agricultural_pest"
        })

    # 2. PlantVillage Solanaceae Healthy Foliage (N=300: 100 Tomato, 100 Pepper, 100 Potato)
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
                    "sample_id": f"healthy_solanaceae_{h_idx:04d}",
                    "source_path": os.path.join(dpath, f),
                    "image_obj": None,
                    "domain": "healthy_solanaceae",
                    "botanical_family": "solanaceae",
                    "ground_truth_label": f"Healthy_{host}",
                    "ground_truth_idx": -1,
                    "plant_host": host.lower()
                })
                h_idx += 1

    # 3. PlantVillage Non-Solanaceae Healthy Foliage (N=250: 50 Strawberry, 50 Soybean, 50 Corn, 50 Grape, 50 Apple)
    non_sol_base = os.path.join(REPO_ROOT, "datasets", "plant_diseases", "non_solanaceae_healthy")
    non_sol_cfgs = [
        ("Strawberry", "strawberry", "rosaceae", 50),
        ("Soybean", "soybean", "fabaceae", 50),
        ("Corn", "corn", "poaceae", 50),
        ("Grape", "grape", "vitaceae", 50),
        ("Apple", "apple", "rosaceae", 50)
    ]
    ns_idx = 0
    for host_name, folder, family, count in non_sol_cfgs:
        dpath = os.path.join(non_sol_base, folder)
        if os.path.exists(dpath):
            files = sorted([f for f in os.listdir(dpath) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            chosen = random.sample(files, min(count, len(files)))
            for f in chosen:
                samples.append({
                    "sample_id": f"healthy_non_solanaceae_{ns_idx:04d}",
                    "source_path": os.path.join(dpath, f),
                    "image_obj": None,
                    "domain": "healthy_non_solanaceae",
                    "botanical_family": family,
                    "ground_truth_label": f"Healthy_{host_name}",
                    "ground_truth_idx": -1,
                    "plant_host": host_name.lower()
                })
                ns_idx += 1

    # 4. PlantVillage Solanaceae Disease Foliage (N=350: 7 classes x 50 samples)
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
                    "botanical_family": "solanaceae",
                    "ground_truth_label": label,
                    "ground_truth_idx": -2,
                    "plant_host": host.lower()
                })
                d_idx += 1

    # 5. Non-Plant Controls (N=51: UI icon + synthetic controls)
    np_idx = 0
    ui_path = os.path.join(REPO_ROOT, "frontend", "src", "app", "icon.png")
    if os.path.exists(ui_path):
        samples.append({
            "sample_id": f"non_plant_{np_idx:04d}",
            "source_path": ui_path,
            "image_obj": None,
            "domain": "non_plant",
            "botanical_family": "none",
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
            "botanical_family": "none",
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
            "botanical_family": "none",
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
            "botanical_family": "none",
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
            "botanical_family": "none",
            "ground_truth_label": "Geometric_Gradient_Control",
            "ground_truth_idx": -3,
            "plant_host": "none"
        })
        np_idx += 1

    return samples

def compute_model_outputs(samples, pest_engine, disease_engine):
    """Runs a single forward pass per model per sample and caches raw logits, energy, and predictions."""
    print(f"Caching forward passes for {len(samples)} samples...")
    raw_results = []
    
    for idx, s in enumerate(samples):
        if idx % 300 == 0:
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
            logits = pest_engine.model(tensor)[0]
            probs = torch.softmax(logits, dim=0)
            top_scores, top_indices = torch.topk(probs, 5)

        logits_np = logits.cpu().numpy()
        top_indices = top_indices.cpu().tolist()
        top_scores = [float(x) for x in top_scores.cpu().tolist()]

        p_idx = top_indices[0]
        p_score = top_scores[0]
        p_name = pest_engine.id_to_name.get(p_idx, f"Class {p_idx}")
        p_mapping = pest_engine.terrace_mappings.get(p_idx, {})
        p_taxonomy = p_mapping.get("status", "unsupported")
        p_family = p_mapping.get("target_pest_family")

        # OOD Statistics
        max_logit = float(np.max(logits_np))
        # Free Energy: -E(x) = T * log(sum(exp(z_i / T)))
        neg_energy = float(np.log(np.sum(np.exp(logits_np))))
        # Softmax Entropy: H(p) = -sum(p * log(p))
        entropy = float(-np.sum(probs.cpu().numpy() * np.log(probs.cpu().numpy() + 1e-12)))

        is_top1_correct = (s["ground_truth_idx"] == p_idx) if s["domain"] == "genuine_pest" else False
        is_top5_correct = (s["ground_truth_idx"] in top_indices) if s["domain"] == "genuine_pest" else False

        # 2. Plant Disease Inference (raw forward pass)
        dis_preds = disease_engine.predict(img)
        top_dis = dis_preds[0] if dis_preds else {"class_raw": "None", "probability": 0.0}
        dis_name = top_dis["class_raw"]
        dis_prob = float(top_dis["probability"])

        is_solanaceae_disease = False
        if any(term in dis_name for term in ["Bacterial_spot", "Early_blight", "Late_blight", "Leaf_Mold", "Septoria", "Target_Spot", "mosaic_virus", "YellowLeaf"]):
            is_solanaceae_disease = True

        raw_results.append({
            "sample_id": s["sample_id"],
            "domain": s["domain"],
            "botanical_family": s["botanical_family"],
            "ground_truth_label": s["ground_truth_label"],
            "ground_truth_idx": s["ground_truth_idx"],
            "plant_host": s["plant_host"],
            "ip102_top1_idx": p_idx,
            "ip102_top1_name": p_name,
            "ip102_top1_score": round(p_score, 4),
            "max_logit": round(max_logit, 4),
            "neg_energy": round(neg_energy, 4),
            "entropy": round(entropy, 4),
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

def apply_classification_rules(item, strategy_name, tau_val=0.25, tau_cand=0.35, tau_unsup=0.25, 
                               use_energy_ood=False, tau_energy=2.0,
                               use_mls_ood=False, tau_mls=0.8,
                               calibrate_thrips=False, tau_thrips=0.45,
                               disease_gating=False, tau_dis=0.75, tau_suppress_pest=0.45):
    """Applies screening rules under Phase 3.4 experimental strategies."""
    score = item["ip102_top1_score"]
    tax_status = item["ip102_taxonomy_status"]
    neg_energy = item["neg_energy"]
    max_logit = item["max_logit"]

    # 1. Stage 1: OOD Prescreening Gating (if enabled)
    if use_energy_ood and neg_energy < tau_energy:
        return "inconclusive", "ood_energy_suppressed"
    
    if use_mls_ood and max_logit < tau_mls:
        return "inconclusive", "ood_mls_suppressed"

    # 2. Stage 2: Taxonomy Thresholding
    if calibrate_thrips and "Scirtothrips" in item["ip102_top1_name"]:
        # Rebalance microscopic thrips class
        threshold = tau_thrips
    elif tax_status == "validated":
        threshold = tau_val
    elif tax_status == "candidate":
        threshold = tau_cand
    else:  # unsupported
        threshold = tau_unsup

    if score < threshold:
        return "inconclusive", "below_pest_threshold"
    elif tax_status == "unsupported":
        decision_status = "unsupported_class"
    else:
        decision_status = "classified_candidate"

    # 3. Stage 3: Solanaceae Disease Cross-Checking (if enabled)
    disease_suppression = False
    if disease_gating and decision_status in ["classified_candidate", "unsupported_class"]:
        if item["disease_is_solanaceae_pathology"] and item["disease_top1_prob"] >= tau_dis and score < tau_suppress_pest:
            decision_status = "inconclusive"
            disease_suppression = True

    return decision_status, ("disease_vetoed" if disease_suppression else "accepted")

def evaluate_configuration(raw_results, config_name, **rules):
    """Evaluates all primary metrics across all sample groups for a specific strategy."""
    pests = [r for r in raw_results if r["domain"] == "genuine_pest"]
    h_sol = [r for r in raw_results if r["domain"] == "healthy_solanaceae"]
    h_non = [r for r in raw_results if r["domain"] == "healthy_non_solanaceae"]
    disease = [r for r in raw_results if r["domain"] == "plant_disease"]
    non_plant = [r for r in raw_results if r["domain"] == "non_plant"]

    def run_strategy_on_group(items):
        decisions = []
        suppressions = {"ood": 0, "disease": 0}
        for it in items:
            st, reason = apply_classification_rules(it, config_name, **rules)
            decisions.append((st, it))
            if "ood" in reason:
                suppressions["ood"] += 1
            elif "disease" in reason:
                suppressions["disease"] += 1
        return decisions, suppressions

    pest_decisions, p_supp = run_strategy_on_group(pests)
    h_sol_decisions, hs_supp = run_strategy_on_group(h_sol)
    h_non_decisions, hn_supp = run_strategy_on_group(h_non)
    disease_decisions, d_supp = run_strategy_on_group(disease)
    non_plant_decisions, np_supp = run_strategy_on_group(non_plant)

    # ── Metric A: Pest Acceptance Recall ──
    pest_accepted_total = sum(1 for st, _ in pest_decisions if st in ["classified_candidate", "unsupported_class"])
    pest_accepted_candidate = sum(1 for st, _ in pest_decisions if st == "classified_candidate")
    pest_accepted_unsupported = sum(1 for st, _ in pest_decisions if st == "unsupported_class")
    pest_inconclusive = sum(1 for st, _ in pest_decisions if st == "inconclusive")

    p_rec_tot, p_rec_tot_lo, p_rec_tot_hi = wilson_score_interval(pest_accepted_total, len(pests))
    p_rec_cand, p_rec_cand_lo, p_rec_cand_hi = wilson_score_interval(pest_accepted_candidate, len(pests))

    # ── Metric B: False-Positive Rates ──
    fp_h_sol = sum(1 for st, _ in h_sol_decisions if st in ["classified_candidate", "unsupported_class"])
    fpr_hs, fpr_hs_lo, fpr_hs_hi = wilson_score_interval(fp_h_sol, len(h_sol))

    fp_h_non = sum(1 for st, _ in h_non_decisions if st in ["classified_candidate", "unsupported_class"])
    fpr_hn, fpr_hn_lo, fpr_hn_hi = wilson_score_interval(fp_h_non, len(h_non))

    fp_disease = sum(1 for st, _ in disease_decisions if st in ["classified_candidate", "unsupported_class"])
    fp_disease_cand = sum(1 for st, _ in disease_decisions if st == "classified_candidate")
    fpr_d, fpr_d_lo, fpr_d_hi = wilson_score_interval(fp_disease, len(disease))

    fp_non_plant = sum(1 for st, _ in non_plant_decisions if st in ["classified_candidate", "unsupported_class"])
    fpr_np, fpr_np_lo, fpr_np_hi = wilson_score_interval(fp_non_plant, len(non_plant))

    total_negatives = len(h_sol) + len(h_non) + len(disease) + len(non_plant)
    total_fp = fp_h_sol + fp_h_non + fp_disease + fp_non_plant
    fpr_overall, fpr_ov_lo, fpr_ov_hi = wilson_score_interval(total_fp, total_negatives)

    # ── Metric C: Pest-Presence Precision ──
    # Definition 1: All accepted predictions
    den_def1 = pest_accepted_total + total_fp
    prec_def1, prec_d1_lo, prec_d1_hi = wilson_score_interval(pest_accepted_total, den_def1) if den_def1 > 0 else (0.0, 0.0, 0.0)

    # Definition 2: Strictly candidate predictions
    fp_candidate_total = (sum(1 for st, _ in h_sol_decisions if st == "classified_candidate") +
                          sum(1 for st, _ in h_non_decisions if st == "classified_candidate") +
                          fp_disease_cand + fp_non_plant)
    den_def2 = pest_accepted_candidate + fp_candidate_total
    prec_def2, prec_d2_lo, prec_d2_hi = wilson_score_interval(pest_accepted_candidate, den_def2) if den_def2 > 0 else (0.0, 0.0, 0.0)

    # ── Metric D: Supported-Class Coverage ──
    cov_val = sum(1 for st, it in pest_decisions if st == "classified_candidate" and it["ip102_taxonomy_status"] == "validated")
    cov_cand = sum(1 for st, it in pest_decisions if st == "classified_candidate" and it["ip102_taxonomy_status"] == "candidate")
    cov_unsup = sum(1 for st, it in pest_decisions if st == "unsupported_class")

    # ── Metric E & F: Species-Level Accuracy ──
    correct_top1_all = sum(1 for _, it in pest_decisions if it["is_ip102_top1_correct"])
    acc_top1_all, _, _ = wilson_score_interval(correct_top1_all, len(pests))

    correct_top1_accepted = sum(1 for st, it in pest_decisions if st in ["classified_candidate", "unsupported_class"] and it["is_ip102_top1_correct"])
    spec_prec_accepted, spec_prec_lo, spec_prec_hi = wilson_score_interval(correct_top1_accepted, pest_accepted_total) if pest_accepted_total > 0 else (0.0, 0.0, 0.0)

    # Macro-F1 across 102 classes
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
    abstention_h_sol = sum(1 for st, _ in h_sol_decisions if st == "inconclusive") / len(h_sol)
    abstention_h_non = sum(1 for st, _ in h_non_decisions if st == "inconclusive") / len(h_non)
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
            "healthy_solanaceae": len(h_sol),
            "healthy_non_solanaceae": len(h_non),
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
            "healthy_solanaceae_fp": fp_h_sol,
            "healthy_solanaceae_total": len(h_sol),
            "healthy_solanaceae_fpr": fpr_hs,
            "healthy_solanaceae_fpr_ci95": [fpr_hs_lo, fpr_hs_hi],
            "healthy_non_solanaceae_fp": fp_h_non,
            "healthy_non_solanaceae_total": len(h_non),
            "healthy_non_solanaceae_fpr": fpr_hn,
            "healthy_non_solanaceae_fpr_ci95": [fpr_hn_lo, fpr_hn_hi],
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
            "healthy_solanaceae_inconclusive_rate": round(abstention_h_sol, 4),
            "healthy_non_solanaceae_inconclusive_rate": round(abstention_h_non, 4),
            "disease_inconclusive_rate": round(abstention_disease, 4),
            "non_plant_inconclusive_rate": round(abstention_non_plant, 4)
        },
        "suppression_telemetry": {
            "genuine_pests_suppressed_ood": p_supp["ood"],
            "genuine_pests_suppressed_disease": p_supp["disease"],
            "healthy_sol_suppressed_ood": hs_supp["ood"],
            "healthy_non_sol_suppressed_ood": hn_supp["ood"],
            "disease_fp_suppressed_ood": d_supp["ood"],
            "disease_fp_suppressed_disease": d_supp["disease"]
        },
        "binary_confusion_matrix": {
            "TP": tp,
            "FN": fn,
            "FP": fp,
            "TN": tn
        }
    }

def main():
    print("=" * 75)
    print("PHASE 3.4 CONTROLLED EXPERIMENT: NON-SOLANACEAE FOLIAGE & OOD SCREENING")
    print("=" * 75)

    os.makedirs(EXPERIMENT_DIR, exist_ok=True)

    pest_engine = get_ip102_engine()
    pest_engine.load_artifacts()

    disease_engine = PlantDiseaseDeepLearningEngine()

    # 1. Collect all 1,971 samples
    samples = collect_evaluation_samples(seed=42)
    print(f"Total evaluation samples collected: {len(samples)}")
    print(f"  Pests: {sum(1 for s in samples if s['domain']=='genuine_pest')}")
    print(f"  Healthy Solanaceae: {sum(1 for s in samples if s['domain']=='healthy_solanaceae')}")
    print(f"  Healthy Non-Solanaceae: {sum(1 for s in samples if s['domain']=='healthy_non_solanaceae')}")
    print(f"  Plant Disease: {sum(1 for s in samples if s['domain']=='plant_disease')}")
    print(f"  Non-Plant Controls: {sum(1 for s in samples if s['domain']=='non_plant')}")

    # 2. Compute forward passes and cache logits, energy, and predictions
    raw_results = compute_model_outputs(samples, pest_engine, disease_engine)

    # 3. Define Configurations
    configs = [
        # Reference Baseline: Phase 3.3 Strategy C1
        ("Baseline (Phase 3.3 C1)", {
            "tau_val": 0.25, "tau_cand": 0.35, "tau_unsup": 0.25,
            "disease_gating": True, "tau_dis": 0.75, "tau_suppress_pest": 0.45,
            "use_energy_ood": False, "use_mls_ood": False, "calibrate_thrips": False
        }),
        
        # Strategy D1: Energy-Based OOD Screening (-E(x) >= 2.0)
        ("Strategy D1 (Energy OOD: tau_E=2.0)", {
            "tau_val": 0.25, "tau_cand": 0.35, "tau_unsup": 0.25,
            "disease_gating": True, "tau_dis": 0.75, "tau_suppress_pest": 0.45,
            "use_energy_ood": True, "tau_energy": 2.0, "use_mls_ood": False, "calibrate_thrips": False
        }),

        # Strategy D2: Max Logit Score (MLS) Screening (max_logit >= 0.8)
        ("Strategy D2 (MLS OOD: tau_mls=0.8)", {
            "tau_val": 0.25, "tau_cand": 0.35, "tau_unsup": 0.25,
            "disease_gating": True, "tau_dis": 0.75, "tau_suppress_pest": 0.45,
            "use_energy_ood": False, "use_mls_ood": True, "tau_mls": 0.8, "calibrate_thrips": False
        }),

        # Strategy D3: Calibrated Microscopic Pest Gating (Thrips tau=0.45)
        ("Strategy D3 (Calibrated Thrips: tau=0.45)", {
            "tau_val": 0.25, "tau_cand": 0.35, "tau_unsup": 0.25,
            "disease_gating": True, "tau_dis": 0.75, "tau_suppress_pest": 0.45,
            "use_energy_ood": False, "use_mls_ood": False, "calibrate_thrips": True, "tau_thrips": 0.45
        }),

        # Strategy D4: Multi-Stage Integrated Architecture (Energy OOD + Calibrated Thrips + Disease Gating)
        ("Strategy D4 (Multi-Stage Integrated Architecture)", {
            "tau_val": 0.25, "tau_cand": 0.35, "tau_unsup": 0.25,
            "disease_gating": True, "tau_dis": 0.75, "tau_suppress_pest": 0.45,
            "use_energy_ood": True, "tau_energy": 2.0, "use_mls_ood": False,
            "calibrate_thrips": True, "tau_thrips": 0.45
        }),
    ]

    all_config_results = {}
    for name, params in configs:
        print(f"\nEvaluating Configuration: {name}...")
        res = evaluate_configuration(raw_results, name, **params)
        all_config_results[name] = res
        print(f"  Pest Acceptance Recall: {res['metric_a_acceptance_recall']['total_accepted_recall']*100:.2f}% ({res['metric_a_acceptance_recall']['total_accepted_pests']}/1020)")
        print(f"  Healthy Solanaceae FPR: {res['metric_b_false_positive_rates']['healthy_solanaceae_fpr']*100:.2f}% ({res['metric_b_false_positive_rates']['healthy_solanaceae_fp']}/300)")
        print(f"  Healthy Non-Solanaceae FPR: {res['metric_b_false_positive_rates']['healthy_non_solanaceae_fpr']*100:.2f}% ({res['metric_b_false_positive_rates']['healthy_non_solanaceae_fp']}/250)")
        print(f"  Disease Foliage FPR: {res['metric_b_false_positive_rates']['disease_fpr']*100:.2f}% ({res['metric_b_false_positive_rates']['disease_fp']}/350)")
        print(f"  Overall Non-Pest FPR: {res['metric_b_false_positive_rates']['overall_fpr']*100:.2f}% ({res['metric_b_false_positive_rates']['overall_fp']}/951)")
        print(f"  Precision Def 1 (All Accepted): {res['metric_c_pest_presence_precision']['def1_all_accepted_precision']*100:.2f}%")
        print(f"  Precision Def 2 (Candidate Only): {res['metric_c_pest_presence_precision']['def2_candidate_only_precision']*100:.2f}%")
        print(f"  Species Correctness among Accepted: {res['metric_f_accepted_species_correctness']['species_accuracy_among_accepted']*100:.2f}%")

    # 4. Save per-image results CSV
    csv_path = os.path.join(EXPERIMENT_DIR, "phase_3_4_per_image_results.csv")
    print(f"\nWriting per-image evaluation results to {csv_path}...")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "sample_id", "domain", "botanical_family", "ground_truth_label", "ground_truth_idx", "plant_host",
            "ip102_top1_idx", "ip102_top1_name", "ip102_top1_score", "max_logit", "neg_energy", "entropy",
            "ip102_taxonomy_status", "is_ip102_top1_correct",
            "status_baseline_c1", "status_strategy_d1", "status_strategy_d2", "status_strategy_d3", "status_strategy_d4"
        ])
        for it in raw_results:
            st_c1, _ = apply_classification_rules(it, "c1", **configs[0][1])
            st_d1, _ = apply_classification_rules(it, "d1", **configs[1][1])
            st_d2, _ = apply_classification_rules(it, "d2", **configs[2][1])
            st_d3, _ = apply_classification_rules(it, "d3", **configs[3][1])
            st_d4, _ = apply_classification_rules(it, "d4", **configs[4][1])

            writer.writerow([
                it["sample_id"], it["domain"], it["botanical_family"], it["ground_truth_label"], it["ground_truth_idx"], it["plant_host"],
                it["ip102_top1_idx"], it["ip102_top1_name"], it["ip102_top1_score"], it["max_logit"], it["neg_energy"], it["entropy"],
                it["ip102_taxonomy_status"], it["is_ip102_top1_correct"],
                st_c1, st_d1, st_d2, st_d3, st_d4
            ])

    # 5. Save machine-readable results JSON
    final_output = {
        "metadata": {
            "title": "Phase 3.4 Controlled Experiment: Non-Solanaceae Foliage & Open-Set OOD Screening",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "evaluation_samples_total": len(raw_results),
            "ip102_checkpoint": "best_checkpoint.pt",
            "disease_model": "model_scripted.pt",
            "device": "CPU"
        },
        "configurations": all_config_results
    }

    json_path = os.path.join(EXPERIMENT_DIR, "phase_3_4_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    print(f"\nSaved machine-readable results to {json_path}")
    print("=" * 75)
    print("PHASE 3.4 CONTROLLED EXPERIMENT COMPLETED SUCCESSFULLY")
    print("=" * 75)

if __name__ == "__main__":
    main()
