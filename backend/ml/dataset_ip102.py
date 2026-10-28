"""IP102 Agricultural Pest Dataset Loader & Preprocessing Pipeline.

Provides robust, reproducible PyTorch Dataset and DataLoader abstractions
for the benchmark IP102 dataset (Xiaoping Wu et al., CVPR 2019).
Supports strict split isolation, error handling for corrupt files,
and standard ImageNet normalization.
"""

import os
import logging
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image

import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T

logger = logging.getLogger(__name__)

# Standard ImageNet normalization coefficients
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def load_ip102_class_mapping(classes_file_path: str) -> Tuple[List[str], Dict[int, str], Dict[str, int]]:
    """Loads classes.txt and builds 0-indexed mapping to class names.
    
    The official IP102 classes.txt contains 102 lines formatted as:
    '<1-based id>  <class_name>'
    In train.txt, val.txt, and test.txt, labels are 0-indexed integers (0..101).
    """
    if not os.path.exists(classes_file_path):
        raise FileNotFoundError(f"Classes file not found at: {classes_file_path}")

    class_names: List[str] = []
    with open(classes_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            # Format: '1  rice leaf roller' or '102 Cicadellidae'
            parts = line_str.split(None, 1)
            if len(parts) == 2:
                class_names.append(parts[1].strip())
            else:
                class_names.append(parts[0].strip())

    id_to_name: Dict[int, str] = {i: name for i, name in enumerate(class_names)}
    name_to_id: Dict[str, int] = {name: i for i, name in enumerate(class_names)}
    return class_names, id_to_name, name_to_id


def get_ip102_transforms(split: str, img_size: int = 224) -> T.Compose:
    """Returns standard preprocessing transforms for IP102 images.
    
    Training: RandomResizedCrop, RandomHorizontalFlip, ColorJitter, Normalization.
    Validation/Test: Resize(256), CenterCrop(224), Normalization (deterministic, no random ops).
    """
    if split == "train":
        return T.Compose([
            T.Resize((256, 256)),
            T.RandomResizedCrop(img_size, scale=(0.8, 1.0)),
            T.RandomHorizontalFlip(p=0.5),
            T.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
            T.ToTensor(),
            T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])
    else:
        return T.Compose([
            T.Resize((256, 256)),
            T.CenterCrop(img_size),
            T.ToTensor(),
            T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])


class IP102Dataset(Dataset):
    """PyTorch Dataset loading images from official IP102 split annotations."""

    def __init__(
        self,
        dataset_root: str,
        split: str,
        transform: Optional[T.Compose] = None,
        max_samples_per_class: Optional[int] = None,
        max_total_samples: Optional[int] = None,
        random_seed: int = 42
    ):
        """Args:
            dataset_root: Root directory of IP102 dataset (containing classes.txt, train.txt, etc.)
            split: 'train', 'val', or 'test'
            transform: torchvision Compose transform pipeline
            max_samples_per_class: Optional limit for balanced subset training
            max_total_samples: Optional cap on total loaded samples
            random_seed: Random seed for deterministic sample subsampling
        """
        self.dataset_root = os.path.abspath(dataset_root)
        self.split = split.lower().strip()
        self.transform = transform or get_ip102_transforms(self.split)

        classes_path = os.path.join(self.dataset_root, "classes.txt")
        self.class_names, self.id_to_name, self.name_to_id = load_ip102_class_mapping(classes_path)
        self.num_classes = len(self.class_names)

        split_file = os.path.join(self.dataset_root, f"{self.split}.txt")
        if not os.path.exists(split_file):
            raise FileNotFoundError(f"Split annotation file not found: {split_file}")

        self.samples: List[Tuple[str, int]] = []
        class_samples: Dict[int, List[str]] = {c: [] for c in range(self.num_classes)}

        with open(split_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    img_name, label_idx = parts[0], int(parts[1])
                    if 0 <= label_idx < self.num_classes:
                        class_samples[label_idx].append(img_name)

        # Assemble samples with optional per-class limit
        for c in range(self.num_classes):
            files = class_samples[c]
            if max_samples_per_class is not None and len(files) > max_samples_per_class:
                # Deterministic shuffle
                g = torch.Generator().manual_seed(random_seed + c)
                indices = torch.randperm(len(files), generator=g)[:max_samples_per_class].tolist()
                files = [files[i] for i in indices]

            for fname in files:
                # Check expected location at classification/{split}/{label}/{filename}
                img_path = os.path.join(self.dataset_root, "classification", self.split, str(c), fname)
                if not os.path.exists(img_path):
                    # Fallback check flat classification/{split}/{filename}
                    alt_path = os.path.join(self.dataset_root, "classification", self.split, fname)
                    if os.path.exists(alt_path):
                        img_path = alt_path

                self.samples.append((img_path, c))

        if max_total_samples is not None and len(self.samples) > max_total_samples:
            g = torch.Generator().manual_seed(random_seed)
            indices = torch.randperm(len(self.samples), generator=g)[:max_total_samples].tolist()
            self.samples = [self.samples[i] for i in indices]

        logger.info(f"Loaded IP102Dataset split '{self.split}': {len(self.samples)} samples across {self.num_classes} classes")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, int]:
        img_path, label = self.samples[index]
        try:
            with Image.open(img_path) as im:
                image = im.convert("RGB")
        except Exception as e:
            logger.warning(f"Failed to open image {img_path}: {e}. Returning zero tensor fallback.")
            image = Image.new("RGB", (224, 224), (0, 0, 0))

        if self.transform:
            tensor = self.transform(image)
        else:
            tensor = T.ToTensor()(image)

        return tensor, label


def create_ip102_dataloaders(
    dataset_root: str,
    batch_size: int = 32,
    num_workers: int = 0,
    max_train_samples: Optional[int] = None,
    max_val_samples: Optional[int] = None,
    max_test_samples: Optional[int] = None
) -> Tuple[DataLoader, DataLoader, DataLoader, List[str]]:
    """Creates isolated PyTorch DataLoaders for train, val, and test splits."""
    train_dataset = IP102Dataset(dataset_root, "train", max_total_samples=max_train_samples)
    val_dataset = IP102Dataset(dataset_root, "val", max_total_samples=max_val_samples)
    test_dataset = IP102Dataset(dataset_root, "test", max_total_samples=max_test_samples)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=False
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=False
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=False
    )

    return train_loader, val_loader, test_loader, train_dataset.class_names
