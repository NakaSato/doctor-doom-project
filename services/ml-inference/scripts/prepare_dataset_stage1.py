#!/usr/bin/env python3
"""
Dataset Preparation Script for Stage 1 Training

Converts dataset_1 annotations to YOLO segmentation format.

Dataset Structure Expected:
    dataset_1/
    ├── images/
    │   ├── 001R.jpg
    │   └── ...
    └── annotations/
        ├── 001R.json
        └── ...

Output:
    datasets/processed/stage1/
    ├── images/
    │   ├── train/
    │   └── val/
    ├── labels/
    │   ├── train/
    │   └── val/
    └── data.yaml
"""
import json
import shutil
from pathlib import Path
import random
from typing import List, Dict, Tuple


def parse_annotation(annotation_path: Path) -> List[Dict]:
    """
    Parse annotation JSON file.
    
    Expected format:
    {
        "instances": [
            {
                "corners": [{"x": x1, "y": y1}, {"x": x2, "y": y2}, ...],
                "center": {"x": cx, "y": cy},
                "defected_module": bool
            }
        ]
    }
    """
    with open(annotation_path) as f:
        data = json.load(f)
    
    instances = []
    for instance in data.get("instances", []):
        corners = instance.get("corners", [])
        if len(corners) >= 4:
            # Extract polygon points
            polygon = [(p["x"], p["y"]) for p in corners]
            is_defected = instance.get("defected_module", False)
            
            instances.append({
                "polygon": polygon,
                "center": instance.get("center", {}),
                "defected": is_defected
            })
    
    return instances


def polygon_to_yolo(polygon: List[Tuple[float, float]], 
                    image_width: int, 
                    image_height: int) -> List[float]:
    """
    Convert polygon to YOLO normalized format.
    
    YOLO segmentation format:
    class x1 y1 x2 y2 x3 y3 ... (normalized 0-1)
    """
    normalized = []
    for x, y in polygon:
        # Normalize to 0-1
        nx = x / image_width
        ny = y / image_height
        
        # Clip to valid range
        nx = max(0, min(1, nx))
        ny = max(0, min(1, ny))
        
        normalized.extend([nx, ny])
    
    return normalized


def get_image_dimensions(image_path: Path) -> Tuple[int, int]:
    """Get image dimensions using PIL."""
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            return img.width, img.height
    except Exception as e:
        print(f"  Warning: Could not read {image_path}: {e}")
        return 640, 512  # Default dimensions


def prepare_dataset(
    dataset_dir: str = "dataset_1",
    output_dir: str = "datasets/processed/stage1",
    val_split: float = 0.2,
    seed: int = 42
):
    """
    Prepare dataset for YOLO segmentation training.
    
    Args:
        dataset_dir: Source dataset directory
        output_dir: Output directory for processed dataset
        val_split: Validation split ratio
        seed: Random seed for reproducibility
    """
    print("=" * 70)
    print("Stage 1 Dataset Preparation")
    print("=" * 70)
    
    dataset_path = Path(dataset_dir)
    output_path = Path(output_dir)
    
    # Check source dataset
    images_dir = dataset_path / "images"
    annotations_dir = dataset_path / "annotations"
    
    if not images_dir.exists():
        print(f"✗ Error: Images directory not found: {images_dir}")
        return False
    
    if not annotations_dir.exists():
        print(f"✗ Error: Annotations directory not found: {annotations_dir}")
        return False
    
    # Get all images
    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
    print(f"\n✓ Found {len(image_files)} images")
    
    # Get all annotations
    annotation_files = list(annotations_dir.glob("*.json"))
    print(f"✓ Found {len(annotation_files)} annotations")
    
    if len(image_files) != len(annotation_files):
        print(f"⚠ Warning: Image/annotation count mismatch")
    
    # Create output directories
    train_images_dir = output_path / "images" / "train"
    val_images_dir = output_path / "images" / "val"
    train_labels_dir = output_path / "labels" / "train"
    val_labels_dir = output_path / "labels" / "val"
    
    for d in [train_images_dir, val_images_dir, train_labels_dir, val_labels_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    print(f"\n✓ Created output directories at {output_path}")
    
    # Split dataset
    random.seed(seed)
    random.shuffle(image_files)
    
    val_size = int(len(image_files) * val_split)
    val_files = image_files[:val_size]
    train_files = image_files[val_size:]
    
    print(f"\n📊 Dataset Split:")
    print(f"   Train: {len(train_files)} images")
    print(f"   Val:   {len(val_files)} images")
    
    # Process function
    def process_image(image_file: Path, split: str):
        """Process single image and annotation."""
        # Get annotation file
        annotation_file = annotations_dir / f"{image_file.stem}.json"
        
        if not annotation_file.exists():
            print(f"  ⚠ No annotation for {image_file.name}")
            return 0
        
        # Get image dimensions
        width, height = get_image_dimensions(image_file)
        
        # Parse annotation
        instances = parse_annotation(annotation_file)
        
        if not instances:
            print(f"  ⚠ No instances in {annotation_file.name}")
            return 0
        
        # Copy image
        if split == "train":
            dest_image = train_images_dir / image_file.name
            dest_label = train_labels_dir / f"{image_file.stem}.txt"
        else:
            dest_image = val_images_dir / image_file.name
            dest_label = val_labels_dir / f"{image_file.stem}.txt"
        
        shutil.copy2(image_file, dest_image)
        
        # Write YOLO label file
        with open(dest_label, "w") as f:
            for instance in instances:
                # Class 0 = solar module (all modules are class 0 for segmentation)
                polygon = instance["polygon"]
                normalized = polygon_to_yolo(polygon, width, height)
                
                # YOLO format: class x1 y1 x2 y2 ...
                line = [0] + normalized
                f.write(" ".join(map(str, line)) + "\n")
        
        return len(instances)
    
    # Process train set
    print(f"\n📝 Processing training set...")
    train_instances = 0
    for img_file in train_files:
        count = process_image(img_file, "train")
        train_instances += count
    
    print(f"✓ Processed {len(train_files)} images, {train_instances} instances")
    
    # Process val set
    print(f"\n📝 Processing validation set...")
    val_instances = 0
    for img_file in val_files:
        count = process_image(img_file, "val")
        val_instances += count
    
    print(f"✓ Processed {len(val_files)} images, {val_instances} instances")
    
    # Create data.yaml
    data_yaml = output_path / "data.yaml"
    yaml_content = f"""# Stage 1: Module Segmentation Dataset
# Generated from dataset_1

path: {output_path.absolute()}
train: images/train
val: images/val

# Classes
nc: 1
names:
  0: solar_module

# Dataset statistics
stats:
  train_images: {len(train_files)}
  val_images: {len(val_files)}
  train_instances: {train_instances}
  val_instances: {val_instances}
  total_instances: {train_instances + val_instances}
"""
    
    with open(data_yaml, "w") as f:
        f.write(yaml_content)
    
    print(f"\n✓ Created data.yaml")
    
    # Summary
    print("\n" + "=" * 70)
    print("DATASET PREPARATION COMPLETE")
    print("=" * 70)
    print(f"\n📁 Output directory: {output_path.absolute()}")
    print(f"📊 Total images: {len(image_files)}")
    print(f"📊 Total instances: {train_instances + val_instances}")
    print(f"\n📋 Next steps:")
    print(f"   1. Review dataset: ls {output_path}/images/train")
    print(f"   2. Train Stage 1:")
    print(f"      python scripts/train_stage1.py \\")
    print(f"          --data {output_path}/data.yaml \\")
    print(f"          --epochs 200 \\")
    print(f"          --batch-size 32 \\")
    print(f"          --device 0")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Prepare dataset for Stage 1 training")
    parser.add_argument("--dataset", type=str, default="dataset_1", help="Source dataset directory")
    parser.add_argument("--output", type=str, default="datasets/processed/stage1", help="Output directory")
    parser.add_argument("--val-split", type=float, default=0.2, help="Validation split ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    success = prepare_dataset(
        dataset_dir=args.dataset,
        output_dir=args.output,
        val_split=args.val_split,
        seed=args.seed
    )
    
    exit(0 if success else 1)
