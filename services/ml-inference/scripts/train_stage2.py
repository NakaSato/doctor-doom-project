#!/usr/bin/env python3
"""
Stage 2: Defect Detection Training Script

Trains YOLOv8m for 12-class defect detection in solar modules.

Usage:
    python train_stage2.py --data datasets/processed/stage2 --epochs 300 --batch-size 32
"""
import argparse
import yaml
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description='Train Stage 2: Defect Detection')
    parser.add_argument('--data', type=str, required=True, help='Path to dataset')
    parser.add_argument('--epochs', type=int, default=300, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--imgsz', type=int, default=128, help='Image size')
    parser.add_argument('--device', type=str, default='0', help='CUDA device')
    parser.add_argument('--workers', type=int, default=8, help='Number of workers')
    parser.add_argument('--name', type=str, default='stage2_defects', help='Experiment name')
    parser.add_argument('--pretrained', action='store_true', default=True, help='Use pretrained weights')
    parser.add_argument('--project', type=str, default='runs/detect', help='Project directory')
    parser.add_argument('--weights', type=str, default='yolov8m.pt', help='Initial weights')
    return parser.parse_args()


def load_config():
    """Load training configuration."""
    config = {
        'model': {
            'architecture': 'yolov8m',
            'pretrained': True,
            'input_size': [128, 128],
            'num_classes': 12,
        },
        'training': {
            'epochs': 300,
            'batch_size': 32,
            'learning_rate': 0.001,
            'weight_decay': 0.05,
            'optimizer': 'AdamW',
            'scheduler': 'CosineAnnealingLR',
        },
        'losses': {
            'box': 'CIoU',
            'cls': 'FocalLoss',
            'focal_alpha': 0.25,
            'focal_gamma': 2.0,
        },
        'augmentation': {
            'mosaic': 1.0,
            'mixup': 0.2,
            'copy_paste': 0.7,
            'cutout': {
                'n_holes': 8,
                'length': 16,
            }
        }
    }
    return config


def train(args, config):
    """Train the defect detection model."""
    print("=" * 70)
    print("Stage 2: Defect Detection Training")
    print("=" * 70)
    print()
    
    # Create project directory
    project_dir = Path(args.project) / args.name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Save config
    config_path = project_dir / 'config.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f, indent=2)
    print(f"✓ Config saved to: {config_path}")
    
    # Load model
    if config['model']['pretrained']:
        print(f"✓ Loading pretrained {config['model']['architecture']} model...")
        model = YOLO(args.weights)
    else:
        print("✓ Creating new YOLOv8m model...")
        model = YOLO('yolov8m.yaml')
    
    # Training arguments
    train_args = {
        'data': f'{args.data}/data.yaml',
        'epochs': args.epochs,
        'batch': args.batch_size,
        'imgsz': args.imgsz,
        'device': args.device,
        'workers': args.workers,
        'project': args.project,
        'name': args.name,
        'patience': 50,
        'verbose': True,
        'save': True,
        'plots': True,
        'exist_ok': True,
        # Class weights for imbalance
        'classes': list(range(12)),
    }
    
    print()
    print("Training Configuration:")
    print(f"  Dataset: {args.data}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch Size: {args.batch_size}")
    print(f"  Image Size: {args.imgsz}")
    print(f"  Device: {args.device}")
    print(f"  Classes: 12 defect types")
    print()
    
    # Train
    print("Starting training...")
    print("-" * 70)
    
    results = model.train(**train_args)
    
    # Export models
    print()
    print("Exporting models...")
    model.export(format='onnx', opset=17)
    print("  ✓ ONNX model exported")
    
    print()
    print("=" * 70)
    print("Training Complete!")
    print("=" * 70)
    print()
    
    # Validate
    print("Running validation...")
    metrics = model.val()
    
    print()
    print("Validation Metrics:")
    print(f"  mAP@50: {metrics.box.map50 * 100:.1f}%")
    print(f"  mAP@50-95: {metrics.box.map * 100:.1f}%")
    print(f"  Precision: {metrics.box.mp * 100:.1f}%")
    print(f"  Recall: {metrics.box.mr * 100:.1f}%")
    print()
    
    # Per-class metrics
    print("Per-Class Metrics:")
    class_names = ['hotspot', 'cell_anomaly', 'delamination', 'diode_failure',
                   'crack', 'soiling', 'discoloration', 'snail_track',
                   'burn_mark', 'corrosion', 'potential_induced', 'broken_cell']
    
    for i, name in enumerate(class_names):
        if i < len(metrics.box.maps):
            print(f"  {name:20s}: mAP@50 = {metrics.box.maps[i] * 100:.1f}%")
    
    print()
    
    return results


def main():
    args = parse_args()
    config = load_config()
    
    # Override config with args
    config['training']['epochs'] = args.epochs
    config['training']['batch_size'] = args.batch_size
    config['model']['input_size'] = [args.imgsz, args.imgsz]
    
    # Train
    results = train(args, config)
    
    print("✓ Training finished successfully!")


if __name__ == '__main__':
    main()
