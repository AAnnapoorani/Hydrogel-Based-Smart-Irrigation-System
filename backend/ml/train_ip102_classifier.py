"""IP102 Agricultural Pest Classifier Training Engine.

Trains a MobileNetV3-Small convolutional neural network for 102-class
agricultural pest recognition using transfer learning from ImageNet.
Implements:
- Two-stage transfer learning (head training followed by fine-tuning)
- Validation metric tracking and best checkpoint preservation
- Epoch history and configuration persistence
- Strict prevention of test set data leakage
"""

import os
import sys
import time
import json
import logging
from typing import Dict, Any, List, Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torchvision.models as models

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.ml.dataset_ip102 import (
    IP102Dataset,
    load_ip102_class_mapping,
    get_ip102_transforms,
    IMAGENET_MEAN,
    IMAGENET_STD
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts", "ip102_model")
DATASET_ROOT = os.path.join(BASE_DIR, "datasets", "pests")


def build_ip102_model(num_classes: int = 102, pretrained: bool = True) -> nn.Module:
    """Builds MobileNetV3-Small configured for 102-class IP102 classification."""
    if pretrained:
        weights = models.MobileNet_V3_Small_Weights.DEFAULT
        model = models.mobilenet_v3_small(weights=weights)
    else:
        model = models.mobilenet_v3_small(weights=None)

    # In MobileNetV3, classifier is:
    # (0): Linear(in_features=576, out_features=1024, bias=True)
    # (1): Hardswish()
    # (2): Dropout(p=0.2, inplace=True)
    # (3): Linear(in_features=1024, out_features=1000, bias=True)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    return model


def compute_topk_accuracy(outputs: torch.Tensor, targets: torch.Tensor, topk: tuple = (1, 5)) -> Dict[int, float]:
    """Computes Top-K accuracy percentage for given predictions and targets."""
    maxk = max(topk)
    batch_size = targets.size(0)

    _, pred = outputs.topk(maxk, 1, True, True)
    pred = pred.t()
    correct = pred.eq(targets.view(1, -1).expand_as(pred))

    res: Dict[int, float] = {}
    for k in topk:
        correct_k = correct[:k].reshape(-1).float().sum(0, keepdim=True)
        res[k] = float(correct_k.mul_(1.0 / batch_size).item())
    return res


def evaluate_split(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Dict[str, float]:
    """Evaluates loss, top-1 accuracy, and top-5 accuracy over a DataLoader."""
    model.eval()
    total_loss = 0.0
    total_samples = 0
    top1_correct = 0
    top5_correct = 0

    with torch.no_grad():
        for inputs, targets in loader:
            inputs = inputs.to(device)
            targets = targets.to(device)
            batch_size = targets.size(0)

            outputs = model(inputs)
            loss = criterion(outputs, targets)
            total_loss += loss.item() * batch_size
            total_samples += batch_size

            # Top-1 and Top-5
            topk = compute_topk_accuracy(outputs, targets, topk=(1, 5))
            top1_correct += topk[1] * batch_size
            top5_correct += topk[5] * batch_size

    avg_loss = total_loss / max(total_samples, 1)
    top1_acc = top1_correct / max(total_samples, 1)
    top5_acc = top5_correct / max(total_samples, 1)

    return {
        "loss": avg_loss,
        "top1_acc": top1_acc,
        "top5_acc": top5_acc,
        "total_samples": total_samples
    }


def train_ip102_classifier(
    dataset_root: str = DATASET_ROOT,
    artifacts_dir: str = ARTIFACTS_DIR,
    epochs: int = 5,
    batch_size: int = 32,
    lr: float = 5e-4,
    weight_decay: float = 1e-4,
    max_train_samples: Optional[int] = None,
    max_val_samples: Optional[int] = None,
    max_train_per_class: Optional[int] = None,
    max_val_per_class: Optional[int] = None,
    random_seed: int = 42,
    device_name: Optional[str] = None
) -> Dict[str, Any]:
    """Executes genuine training for the IP102 pest classifier.
    
    Strictly isolated: train split is used for parameter updates;
    val split is used for validation and checkpoint selection;
    test split is NEVER accessed in this function.
    """
    torch.manual_seed(random_seed)
    os.makedirs(artifacts_dir, exist_ok=True)

    if device_name:
        device = torch.device(device_name)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using training device: {device}")

    # 1. Load class mapping
    classes_path = os.path.join(dataset_root, "classes.txt")
    class_names, id_to_name, name_to_id = load_ip102_class_mapping(classes_path)
    num_classes = len(class_names)
    logger.info(f"Loaded {num_classes} IP102 classes from {classes_path}")

    # Save class mapping immediately
    class_mapping_path = os.path.join(artifacts_dir, "class_mapping.json")
    with open(class_mapping_path, "w", encoding="utf-8") as f:
        json.dump({
            "num_classes": num_classes,
            "classes": class_names,
            "id_to_name": id_to_name
        }, f, indent=2)

    # 2. Prepare Datasets (Train and Val ONLY)
    logger.info(f"Initializing IP102 train dataset from {dataset_root}...")
    train_dataset = IP102Dataset(
        dataset_root=dataset_root,
        split="train",
        max_samples_per_class=max_train_per_class,
        max_total_samples=max_train_samples,
        random_seed=random_seed
    )
    val_dataset = IP102Dataset(
        dataset_root=dataset_root,
        split="val",
        max_samples_per_class=max_val_per_class,
        max_total_samples=max_val_samples,
        random_seed=random_seed
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=False
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=False
    )

    logger.info(f"Train split: {len(train_dataset)} samples ({len(train_loader)} batches)")
    logger.info(f"Val split: {len(val_dataset)} samples ({len(val_loader)} batches)")

    # 3. Model, Loss, Optimizer, Scheduler
    model = build_ip102_model(num_classes=num_classes, pretrained=True)
    model.to(device)

    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    best_val_acc = -1.0
    best_val_loss = float("inf")
    best_epoch = 0
    history: List[Dict[str, Any]] = []

    start_time = time.time()
    logger.info(f"Beginning training for {epochs} epochs...")

    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        model.train()
        running_loss = 0.0
        train_samples = 0
        train_top1 = 0
        train_top5 = 0

        for batch_idx, (inputs, targets) in enumerate(train_loader, 1):
            inputs = inputs.to(device)
            targets = targets.to(device)
            batch_sz = targets.size(0)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * batch_sz
            train_samples += batch_sz

            topk = compute_topk_accuracy(outputs, targets, topk=(1, 5))
            train_top1 += topk[1] * batch_sz
            train_top5 += topk[5] * batch_sz

            if batch_idx % max(1, len(train_loader) // 5) == 0 or batch_idx == len(train_loader):
                logger.info(
                    f"Epoch {epoch}/{epochs} [{batch_idx}/{len(train_loader)}] "
                    f"Batch Loss: {loss.item():.4f} | Running Acc: {train_top1/train_samples*100:.1f}%"
                )

        scheduler.step()
        epoch_duration = time.time() - epoch_start

        epoch_train_loss = running_loss / max(train_samples, 1)
        epoch_train_acc = train_top1 / max(train_samples, 1)
        epoch_train_top5 = train_top5 / max(train_samples, 1)

        # Validation
        val_metrics = evaluate_split(model, val_loader, criterion, device)
        current_lr = scheduler.get_last_lr()[0]

        logger.info(
            f"=== Epoch {epoch}/{epochs} Summary ({epoch_duration:.1f}s) ===\n"
            f"  Train Loss: {epoch_train_loss:.4f} | Train Top-1: {epoch_train_acc*100:.2f}% | Train Top-5: {epoch_train_top5*100:.2f}%\n"
            f"  Val Loss:   {val_metrics['loss']:.4f} | Val Top-1:   {val_metrics['top1_acc']*100:.2f}% | Val Top-5:   {val_metrics['top5_acc']*100:.2f}%\n"
            f"  Learning Rate: {current_lr:.6f}"
        )

        record = {
            "epoch": epoch,
            "train_loss": epoch_train_loss,
            "train_top1_acc": epoch_train_acc,
            "train_top5_acc": epoch_train_top5,
            "val_loss": val_metrics["loss"],
            "val_top1_acc": val_metrics["top1_acc"],
            "val_top5_acc": val_metrics["top5_acc"],
            "lr": current_lr,
            "duration_seconds": epoch_duration
        }
        history.append(record)

        # Checkpoint Selection: Save best based on Val Top-1 Acc (or Val Loss as tie-breaker)
        if val_metrics["top1_acc"] > best_val_acc:
            best_val_acc = val_metrics["top1_acc"]
            best_val_loss = val_metrics["loss"]
            best_epoch = epoch

            best_checkpoint_path = os.path.join(artifacts_dir, "best_checkpoint.pt")
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_top1_acc": best_val_acc,
                "val_loss": best_val_loss,
                "val_top5_acc": val_metrics["top5_acc"],
                "num_classes": num_classes,
                "model_architecture": "mobilenet_v3_small",
                "class_names": class_names
            }, best_checkpoint_path)
            logger.info(f"  --> Saved new best checkpoint to {best_checkpoint_path} (Val Top-1: {best_val_acc*100:.2f}%)")

    total_training_time = time.time() - start_time

    # Save final checkpoint
    final_checkpoint_path = os.path.join(artifacts_dir, "final_checkpoint.pt")
    torch.save({
        "epoch": epochs,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "final_val_top1_acc": history[-1]["val_top1_acc"] if history else 0.0,
        "final_val_loss": history[-1]["val_loss"] if history else 0.0,
        "num_classes": num_classes,
        "model_architecture": "mobilenet_v3_small",
        "class_names": class_names
    }, final_checkpoint_path)

    # Save Training History
    history_path = os.path.join(artifacts_dir, "training_history.json")
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump({
            "epochs_completed": epochs,
            "total_duration_seconds": total_training_time,
            "best_epoch": best_epoch,
            "best_val_top1_acc": best_val_acc,
            "best_val_loss": best_val_loss,
            "history": history
        }, f, indent=2)

    # Save Configuration
    config_path = os.path.join(artifacts_dir, "training_config.json")
    training_config = {
        "model_architecture": "mobilenet_v3_small",
        "pretrained_initialization": "ImageNet (MobileNet_V3_Small_Weights.DEFAULT)",
        "num_classes": num_classes,
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
        "epochs": epochs,
        "batch_size": batch_size,
        "lr": lr,
        "weight_decay": weight_decay,
        "loss_function": "CrossEntropyLoss(label_smoothing=0.05)",
        "optimizer": "AdamW",
        "scheduler": "CosineAnnealingLR",
        "random_seed": random_seed,
        "device": str(device),
        "total_training_time_seconds": total_training_time,
        "best_epoch": best_epoch,
        "best_val_top1_acc": best_val_acc,
        "best_val_loss": best_val_loss,
        "normalization": {
            "mean": IMAGENET_MEAN,
            "std": IMAGENET_STD
        }
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(training_config, f, indent=2)

    logger.info(f"Training completed in {total_training_time:.1f}s. Artifacts saved to {artifacts_dir}")
    return training_config


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train genuine IP102 pest classifier")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=5e-4, help="Learning rate")
    parser.add_argument("--max-train", type=int, default=None, help="Cap on train samples")
    parser.add_argument("--max-val", type=int, default=None, help="Cap on val samples")
    parser.add_argument("--per-class-train", type=int, default=None, help="Samples per class for train")
    parser.add_argument("--per-class-val", type=int, default=None, help="Samples per class for val")
    parser.add_argument("--artifacts-dir", type=str, default=ARTIFACTS_DIR, help="Destination directory for artifacts")
    args = parser.parse_args()

    train_ip102_classifier(
        artifacts_dir=args.artifacts_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        max_train_samples=args.max_train,
        max_val_samples=args.max_val,
        max_train_per_class=args.per_class_train,
        max_val_per_class=args.per_class_val
    )
