"""IP102 Agricultural Pest Classifier Evaluation & Calibration Engine.

Evaluates the trained MobileNetV3-Small classifier on held-out test data:
- Top-1 & Top-5 categorical accuracy
- Macro-F1 score and per-class Precision / Recall
- Multi-class Confusion Matrix
- Expected Calibration Error (ECE) and Reliability Diagram data
- Temperature Scaling calibration fitted strictly on validation logits
"""

import os
import sys
import time
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix, f1_score

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.ml.dataset_ip102 import (
    IP102Dataset,
    load_ip102_class_mapping,
    get_ip102_transforms
)
from backend.ml.train_ip102_classifier import (
    build_ip102_model,
    compute_topk_accuracy
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts", "ip102_model")
DATASET_ROOT = os.path.join(BASE_DIR, "datasets", "pests")


def compute_ece(confidences: np.ndarray, predictions: np.ndarray, targets: np.ndarray, n_bins: int = 15) -> Tuple[float, List[Dict[str, Any]]]:
    """Computes Expected Calibration Error (ECE) and binned reliability data."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total_samples = len(confidences)
    diagram_points: List[Dict[str, Any]] = []

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        # Samples falling into the bin
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper) if i > 0 else (confidences >= bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)

        if np.sum(in_bin) > 0:
            bin_acc = np.mean(predictions[in_bin] == targets[in_bin])
            bin_conf = np.mean(confidences[in_bin])
            bin_count = int(np.sum(in_bin))
            ece += np.abs(bin_acc - bin_conf) * (bin_count / total_samples)

            diagram_points.append({
                "bin_index": i,
                "bin_lower": float(bin_lower),
                "bin_upper": float(bin_upper),
                "count": bin_count,
                "mean_confidence": float(bin_conf),
                "accuracy": float(bin_acc),
                "gap": float(np.abs(bin_acc - bin_conf))
            })
        else:
            diagram_points.append({
                "bin_index": i,
                "bin_lower": float(bin_lower),
                "bin_upper": float(bin_upper),
                "count": 0,
                "mean_confidence": float((bin_lower + bin_upper) / 2.0),
                "accuracy": 0.0,
                "gap": 0.0
            })

    return float(ece), diagram_points


class TemperatureScaler(nn.Module):
    """Calibrates model logits using Temperature Scaling.
    
    Fitted strictly on validation data to prevent test set data leakage.
    """
    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        return logits / self.temperature

    def fit_on_val(self, val_logits: torch.Tensor, val_targets: torch.Tensor, max_iter: int = 50) -> float:
        """Finds optimal temperature T minimizing NLL on validation logits."""
        nll_criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.LBFGS([self.temperature], lr=0.01, max_iter=max_iter)

        def eval_loss():
            optimizer.zero_grad()
            loss = nll_criterion(self.forward(val_logits), val_targets)
            loss.backward()
            return loss

        optimizer.step(eval_loss)
        # Ensure temperature stays strictly positive
        with torch.no_grad():
            self.temperature.clamp_(min=0.05, max=10.0)
        return float(self.temperature.item())


def collect_logits_and_targets(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device
) -> Tuple[torch.Tensor, torch.Tensor, float]:
    """Runs inference across loader and returns raw logits, targets, and avg latency per sample."""
    model.eval()
    all_logits = []
    all_targets = []
    total_time = 0.0
    total_samples = 0

    with torch.no_grad():
        for inputs, targets in loader:
            inputs = inputs.to(device)
            batch_sz = targets.size(0)

            t0 = time.time()
            logits = model(inputs)
            t1 = time.time()

            total_time += (t1 - t0)
            total_samples += batch_sz

            all_logits.append(logits.cpu())
            all_targets.append(targets)

    logits_tensor = torch.cat(all_logits, dim=0)
    targets_tensor = torch.cat(all_targets, dim=0)
    avg_latency_ms = (total_time / max(total_samples, 1)) * 1000.0

    return logits_tensor, targets_tensor, avg_latency_ms


def evaluate_ip102_model(
    checkpoint_path: Optional[str] = None,
    dataset_root: str = DATASET_ROOT,
    artifacts_dir: str = ARTIFACTS_DIR,
    max_test_samples: Optional[int] = None,
    max_val_samples: Optional[int] = None,
    max_test_per_class: Optional[int] = None,
    max_val_per_class: Optional[int] = None,
    batch_size: int = 32,
    device_name: Optional[str] = None
) -> Dict[str, Any]:
    """Runs comprehensive evaluation and calibration analysis on the IP102 classifier."""
    if checkpoint_path is None:
        checkpoint_path = os.path.join(artifacts_dir, "best_checkpoint.pt")
        if not os.path.exists(checkpoint_path):
            checkpoint_path = os.path.join(artifacts_dir, "final_checkpoint.pt")

    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found at: {checkpoint_path}")

    if device_name:
        device = torch.device(device_name)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Evaluating checkpoint: {checkpoint_path} on {device}")

    # Load class mapping
    classes_path = os.path.join(dataset_root, "classes.txt")
    class_names, id_to_name, name_to_id = load_ip102_class_mapping(classes_path)
    num_classes = len(class_names)

    # Load model
    model = build_ip102_model(num_classes=num_classes, pretrained=False)
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    # 1. Validation Split: Used EXCLUSIVELY to fit temperature scaling
    val_dataset = IP102Dataset(
        dataset_root=dataset_root,
        split="val",
        max_samples_per_class=max_val_per_class,
        max_total_samples=max_val_samples
    )
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    logger.info(f"Collecting validation logits from {len(val_dataset)} samples to fit calibration...")
    val_logits, val_targets, _ = collect_logits_and_targets(model, val_loader, device)

    temp_scaler = TemperatureScaler()
    optimal_temperature = temp_scaler.fit_on_val(val_logits, val_targets)
    logger.info(f"Fitted optimal temperature on validation logits: T = {optimal_temperature:.4f}")

    # 2. Test Split: Held-out evaluation
    test_dataset = IP102Dataset(
        dataset_root=dataset_root,
        split="test",
        max_samples_per_class=max_test_per_class,
        max_total_samples=max_test_samples
    )
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    logger.info(f"Evaluating held-out test split: {len(test_dataset)} samples...")

    test_logits, test_targets, avg_latency_ms = collect_logits_and_targets(model, test_loader, device)

    # Uncalibrated predictions
    uncal_probs = F.softmax(test_logits, dim=1).detach().cpu().numpy()
    uncal_confs = np.max(uncal_probs, axis=1)
    uncal_preds = np.argmax(uncal_probs, axis=1)
    targets_np = test_targets.detach().cpu().numpy()

    # Calibrated predictions
    with torch.no_grad():
        cal_logits = temp_scaler(test_logits)
        cal_probs = F.softmax(cal_logits, dim=1).detach().cpu().numpy()
    cal_confs = np.max(cal_probs, axis=1)
    cal_preds = np.argmax(cal_probs, axis=1)

    # Metrics computation
    topk = compute_topk_accuracy(test_logits, test_targets, topk=(1, 5))
    top1_accuracy = float(topk[1])
    top5_accuracy = float(topk[5])
    macro_f1 = float(f1_score(targets_np, uncal_preds, average="macro", zero_division=0))

    # Detailed per-class report
    clf_report_raw = classification_report(
        targets_np,
        uncal_preds,
        labels=list(range(num_classes)),
        target_names=[class_names[i] for i in range(num_classes)],
        output_dict=True,
        zero_division=0
    )
    clf_report: Dict[str, Any] = clf_report_raw if isinstance(clf_report_raw, dict) else {}

    per_class_summary = []
    for idx in range(num_classes):
        cname = class_names[idx]
        metrics = clf_report.get(cname, {"precision": 0.0, "recall": 0.0, "f1-score": 0.0, "support": 0})
        per_class_summary.append({
            "class_id": idx,
            "class_name": cname,
            "precision": float(metrics["precision"]),
            "recall": float(metrics["recall"]),
            "f1_score": float(metrics["f1-score"]),
            "support": int(metrics["support"])
        })

    # Confusion matrix
    conf_mat = confusion_matrix(targets_np, uncal_preds, labels=list(range(num_classes)))

    # Calibration error (pre and post)
    uncal_ece, uncal_diagram = compute_ece(uncal_confs, uncal_preds, targets_np, n_bins=15)
    cal_ece, cal_diagram = compute_ece(cal_confs, cal_preds, targets_np, n_bins=15)

    evaluation_report = {
        "checkpoint_evaluated": os.path.basename(checkpoint_path),
        "test_samples_evaluated": len(test_dataset),
        "val_samples_used_for_calibration": len(val_dataset),
        "num_classes": num_classes,
        "metrics": {
            "top1_accuracy": top1_accuracy,
            "top5_accuracy": top5_accuracy,
            "macro_f1": macro_f1,
            "uncalibrated_ece": uncal_ece,
            "calibrated_ece": cal_ece,
            "optimal_temperature": optimal_temperature,
            "avg_inference_latency_ms": avg_latency_ms
        },
        "calibration": {
            "method": "Temperature Scaling (Validation-fitted)",
            "n_bins": 15,
            "temperature": optimal_temperature,
            "uncalibrated_ece": uncal_ece,
            "calibrated_ece": cal_ece,
            "reliability_diagram": cal_diagram
        },
        "per_class_summary": per_class_summary,
        "confusion_matrix_shape": list(conf_mat.shape),
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Save artifacts
    report_path = os.path.join(artifacts_dir, "evaluation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(evaluation_report, f, indent=2)

    conf_matrix_path = os.path.join(artifacts_dir, "confusion_matrix.json")
    with open(conf_matrix_path, "w", encoding="utf-8") as f:
        json.dump({
            "matrix": conf_mat.tolist(),
            "labels": class_names
        }, f)

    logger.info(
        f"\n=== IP102 Held-Out Test Evaluation Results ===\n"
        f"  Evaluated Test Images: {len(test_dataset)}\n"
        f"  Top-1 Accuracy:        {top1_accuracy*100:.2f}%\n"
        f"  Top-5 Accuracy:        {top5_accuracy*100:.2f}%\n"
        f"  Macro-F1 Score:        {macro_f1:.4f}\n"
        f"  Uncalibrated ECE:      {uncal_ece*100:.2f}%\n"
        f"  Calibrated ECE:        {cal_ece*100:.2f}% (T={optimal_temperature:.3f})\n"
        f"  Avg Latency per Image: {avg_latency_ms:.2f} ms\n"
        f"  Report Saved:          {report_path}"
    )

    return evaluation_report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate IP102 pest classifier")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to checkpoint")
    parser.add_argument("--max-test", type=int, default=None, help="Cap on test samples")
    parser.add_argument("--max-val", type=int, default=None, help="Cap on val samples for calibration")
    parser.add_argument("--per-class-test", type=int, default=None, help="Samples per class for test")
    parser.add_argument("--per-class-val", type=int, default=None, help="Samples per class for val")
    parser.add_argument("--artifacts-dir", type=str, default=ARTIFACTS_DIR, help="Directory containing model artifacts")
    args = parser.parse_args()

    evaluate_ip102_model(
        checkpoint_path=args.checkpoint,
        artifacts_dir=args.artifacts_dir,
        max_test_samples=args.max_test,
        max_val_samples=args.max_val,
        max_test_per_class=args.per_class_test,
        max_val_per_class=args.per_class_val
    )
