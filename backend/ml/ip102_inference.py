"""Dedicated IP102 Pest Classifier Inference Component.

Loads the Phase 2 MobileNetV3-Small 102-class checkpoint and evaluates
agricultural pest imagery for candidate screening.
Features:
- Lazy singleton model initialization with evaluation-mode CPU inference.
- Exact class-index resolution from stratified Phase 2 metadata.
- Separation between raw model predictions and terrace pest-family mappings.
- Explicit uncertainty handling:
  * 'classified_candidate': validated terrace mapping with provisional score >= threshold
  * 'unsupported_class': model predicted class outside validated terrace gardening scope
  * 'inconclusive': confidence below provisional threshold or ambiguous evidence
  * 'model_unavailable': checkpoint or mapping artifact missing/unreadable
- Safe handling of corrupt or invalid image inputs.
- Zero network downloads during inference.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import torch
import torch.nn as nn
import torchvision.transforms as T
import torchvision.models as models

logger = logging.getLogger(__name__)

# Base directory paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts", "ip102_model_v2_stratified")
DEFAULT_MAPPING_PATH = os.path.join(os.path.dirname(__file__), "ip102_terrace_mapping.json")

# Standard ImageNet normalization parameters used during training
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_inference_transforms(img_size: int = 224) -> T.Compose:
    """Returns deterministic evaluation preprocessing transforms."""
    return T.Compose([
        T.Resize((256, 256)),
        T.CenterCrop(img_size),
        T.ToTensor(),
        T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])


class IP102InferenceEngine:
    """Production inference engine for the IP102 102-class agricultural pest classifier."""

    # Provisional operational threshold.
    # Uniform random chance over 102 classes is 1/102 ≈ 0.0098 (0.98%).
    # A softmax score of 0.25 represents >25x random chance and filters out noise
    # while recognizing candidate predictions. Note: uncalibrated softmax score.
    DEFAULT_PROVISIONAL_THRESHOLD: float = 0.25

    def __init__(
        self,
        artifacts_dir: Optional[str] = None,
        mapping_path: Optional[str] = None,
        provisional_threshold: float = DEFAULT_PROVISIONAL_THRESHOLD,
        device: str = "cpu"
    ):
        self.artifacts_dir = artifacts_dir or DEFAULT_ARTIFACTS_DIR
        self.mapping_path = mapping_path or DEFAULT_MAPPING_PATH
        self.provisional_threshold = provisional_threshold
        self.device = torch.device(device)

        self.model: Optional[nn.Module] = None
        self.class_names: List[str] = []
        self.id_to_name: Dict[int, str] = {}
        self.terrace_mappings: Dict[int, Dict[str, Any]] = {}
        self.is_loaded: bool = False
        self.load_error: Optional[str] = None

        self.transforms = get_inference_transforms(img_size=224)

    def load_artifacts(self) -> bool:
        """Loads model weights and class mappings into memory."""
        if self.is_loaded:
            return True

        checkpoint_path = os.path.join(self.artifacts_dir, "best_checkpoint.pt")
        class_mapping_path = os.path.join(self.artifacts_dir, "class_mapping.json")

        # 1. Verify existence of required artifact files
        if not os.path.exists(checkpoint_path):
            self.load_error = f"Checkpoint file missing at {checkpoint_path}"
            logger.warning(self.load_error)
            return False

        if not os.path.exists(class_mapping_path):
            self.load_error = f"Class mapping file missing at {class_mapping_path}"
            logger.warning(self.load_error)
            return False

        try:
            # 2. Load class mapping from trained checkpoint artifact
            with open(class_mapping_path, "r", encoding="utf-8") as f:
                mapping_data = json.load(f)

            if "classes" not in mapping_data or len(mapping_data["classes"]) != 102:
                self.load_error = f"Invalid class mapping: expected 102 classes, found {len(mapping_data.get('classes', []))}"
                logger.error(self.load_error)
                return False

            self.class_names = mapping_data["classes"]
            self.id_to_name = {int(k): v for k, v in mapping_data.get("id_to_name", {}).items()}
            if not self.id_to_name:
                self.id_to_name = {i: name for i, name in enumerate(self.class_names)}

            # 3. Load terrace gardening relevance mapping if available
            if os.path.exists(self.mapping_path):
                with open(self.mapping_path, "r", encoding="utf-8") as f:
                    terrace_data = json.load(f)
                mappings_list = terrace_data.get("mappings", [])
                self.terrace_mappings = {m["class_index"]: m for m in mappings_list}
            else:
                logger.warning(f"Terrace mapping file not found at {self.mapping_path}. Proceeding with default mappings.")
                self.terrace_mappings = {}

            # 4. Construct MobileNetV3-Small architecture without downloading pretrained weights
            model = models.mobilenet_v3_small(weights=None)
            in_features = model.classifier[3].in_features
            model.classifier[3] = nn.Linear(in_features, len(self.class_names))

            # 5. Load state dict from checkpoint
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            state_dict = checkpoint.get("model_state_dict", checkpoint)
            model.load_state_dict(state_dict)

            model.to(self.device)
            model.eval()

            self.model = model
            self.is_loaded = True
            self.load_error = None
            logger.info("IP102 Pest Classifier loaded successfully from %s", checkpoint_path)
            return True

        except Exception as exc:
            self.load_error = f"Failed to load IP102 model checkpoint: {exc}"
            logger.error(self.load_error, exc_info=True)
            self.model = None
            self.is_loaded = False
            return False

    def predict(
        self,
        image: Any,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Runs evaluation-mode inference on a PIL Image.
        
        Returns a structured dictionary with:
        - status: 'classified_candidate', 'unsupported_class', 'inconclusive', 'model_unavailable'
        - raw_index: int (0..101)
        - raw_class_name: str
        - raw_softmax_score: float (0.0 to 1.0)
        - confidence_pct: float (0.0 to 100.0)
        - top5_candidates: list of candidate predictions
        - terrace_family: optional normalized pest family key
        - mapping_status: 'validated', 'candidate', 'unsupported'
        - model_architecture: str
        - is_conclusive: bool (always False for candidate classifications)
        """
        # Ensure model is initialized
        if not self.is_loaded:
            self.load_artifacts()

        if self.model is None:
            return {
                "status": "model_unavailable",
                "raw_index": None,
                "raw_class_name": None,
                "raw_softmax_score": 0.0,
                "confidence_pct": 0.0,
                "top5_candidates": [],
                "terrace_family": None,
                "mapping_status": "unsupported",
                "model_architecture": "IP102 Classifier (Unavailable)",
                "is_conclusive": False,
                "error_message": self.load_error or "Model checkpoint unavailable"
            }

        # 1. Image validation
        if image is None:
            return self._error_result("Input image is None")

        if not isinstance(image, Image.Image):
            try:
                image = Image.fromarray(image)
            except Exception as e:
                return self._error_result(f"Invalid image type: {type(image)} ({e})")

        if image.width < 10 or image.height < 10:
            return self._error_result(f"Image dimensions too small: ({image.width}x{image.height})")

        # 2. Preprocess
        try:
            rgb_image = image.convert("RGB")
            tensor = self.transforms(rgb_image).unsqueeze(0).to(self.device)
        except Exception as e:
            return self._error_result(f"Image preprocessing failed: {e}")

        # 3. Model inference
        try:
            with torch.no_grad():
                logits = self.model(tensor)
                probabilities = torch.softmax(logits, dim=1)[0]
                top_scores, top_indices = torch.topk(probabilities, min(top_k, len(self.class_names)))
        except Exception as e:
            logger.error("Inference execution failed: %s", e)
            return self._error_result(f"Inference execution failed: {e}")

        top_indices_list = top_indices.cpu().tolist()
        top_scores_list = top_scores.cpu().tolist()

        primary_idx = top_indices_list[0]
        primary_score = float(top_scores_list[0])
        primary_name = self.id_to_name.get(primary_idx, f"Class {primary_idx}")

        # 4. Resolve candidate list
        top_candidates = []
        for idx, score in zip(top_indices_list, top_scores_list):
            c_name = self.id_to_name.get(idx, f"Class {idx}")
            t_map = self.terrace_mappings.get(idx, {})
            top_candidates.append({
                "index": idx,
                "class_name": c_name,
                "softmax_score": round(float(score), 4),
                "confidence_pct": round(float(score) * 100, 2),
                "terrace_family": t_map.get("target_pest_family"),
                "mapping_status": t_map.get("status", "unsupported"),
                "terrace_relevance": t_map.get("terrace_relevance", "Unknown")
            })

        # 5. Determine mapping and uncertainty status
        primary_mapping = self.terrace_mappings.get(primary_idx, {})
        mapping_status = primary_mapping.get("status", "unsupported")
        terrace_family = primary_mapping.get("target_pest_family")

        # Status determination logic:
        # A. If softmax score is below provisional threshold -> inconclusive
        if primary_score < self.provisional_threshold:
            status = "inconclusive"
        # B. If mapping status is unsupported -> unsupported_class
        elif mapping_status == "unsupported":
            status = "unsupported_class"
        # C. If mapping status is validated or candidate -> classified_candidate
        else:
            status = "classified_candidate"

        return {
            "status": status,
            "raw_index": primary_idx,
            "raw_class_name": primary_name,
            "raw_softmax_score": round(primary_score, 4),
            "confidence_pct": round(primary_score * 100, 2),
            "top5_candidates": top_candidates,
            "terrace_family": terrace_family,
            "mapping_status": mapping_status,
            "terrace_relevance": primary_mapping.get("terrace_relevance", "Unknown"),
            "model_architecture": "MobileNetV3-Small (IP102 - 102 Classes)",
            "is_conclusive": False,  # Candidate screening only
            "scientific_rationale": primary_mapping.get("rationale", ""),
            "known_limitations": primary_mapping.get("known_limitations", ""),
            "error_message": None
        }

    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """Returns safe default structure on image error."""
        logger.warning("IP102 inference returning safe fallback: %s", error_msg)
        return {
            "status": "inconclusive",
            "raw_index": None,
            "raw_class_name": None,
            "raw_softmax_score": 0.0,
            "confidence_pct": 0.0,
            "top5_candidates": [],
            "terrace_family": None,
            "mapping_status": "unsupported",
            "model_architecture": "MobileNetV3-Small (IP102 - 102 Classes)",
            "is_conclusive": False,
            "error_message": error_msg
        }


# Global lazy singleton instance
_ip102_engine: Optional[IP102InferenceEngine] = None


def get_ip102_engine(
    artifacts_dir: Optional[str] = None,
    mapping_path: Optional[str] = None,
    provisional_threshold: float = IP102InferenceEngine.DEFAULT_PROVISIONAL_THRESHOLD
) -> IP102InferenceEngine:
    """Returns the singleton instance of IP102InferenceEngine."""
    global _ip102_engine
    if _ip102_engine is None:
        _ip102_engine = IP102InferenceEngine(
            artifacts_dir=artifacts_dir,
            mapping_path=mapping_path,
            provisional_threshold=provisional_threshold
        )
    return _ip102_engine
