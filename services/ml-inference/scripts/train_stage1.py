#!/usr/bin/env python3
"""
Stage 1: Module Segmentation Training Script

Trains YOLOv8n-seg for solar module segmentation from thermal imagery.

Usage:
    python train_stage1.py --data datasets/processed/stage1 --epochs 200 --batch-size 32
"""
import argparse
import yaml
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description='Train Stage 1: Module Segmentation')
    parser.add_argument('--data', type=str, required=True, help='Path to dataset')
    parser.add_argument('--epochs', type=int, default=200, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--imgsz', nargs=2, type=int, default=[640, 512], help='Image size')
    parser.add_argument('--device', type=str, default='0', help='CUDA device')
    parser.add_argument('--workers', type=int, default=8, help='Number of workers')
    parser.add_argument('--name', type=str, default='stage1_segmentation', help='Experiment name')
    parser.add_argument('--pretrained', action='store_true', default=True, help='Use pretrained weights')
    parser.add_argument('--project', type=str, default='runs/segment', help='Project directory')
    return parser.parse_args()


def load_config():
    """Load training configuration."""
    config = {
        'model': {
            'architecture': 'yolov8n-seg',
            'pretrained': True,
            'input_size': [640, 512],
            'num_classes': 1,
        },
        'training': {
            'epochs': 200,
            'batch_size': 32,
            'learning_rate': 0.01,
            'weight_decay': 0.0005,
            'optimizer': 'SGD',
            'scheduler': 'CosineAnnealingLR',
        },
        'augmentation': {
            'mosaic': 1.0,
            'mixup': 0.2,
            'affine': {
                'rotation': 15,
                'scale': [0.8, 1.2],
                'translate': 0.1,
                'shear': 10,
            }
        }
    }
    return config


def train(args, config):
    """Train the segmentation model."""
    print("=" * 70)
    print("Stage 1: Module Segmentation Training")
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
        print("✓ Loading pretrained YOLOv8n-seg model...")
        model = YOLO('yolov8n-seg.pt')
    else:
        print("✓ Creating new YOLOv8n-seg model...")
        model = YOLO('yolov8n-seg.yaml')
    
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
    }
    
    print()
    print("Training Configuration:")
    print(f"  Dataset: {args.data}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch Size: {args.batch_size}")
    print(f"  Image Size: {args.imgsz}")
    print(f"  Device: {args.device}")
    print(f"  Workers: {args.workers}")
    print()
    
    # Train
    print("Starting training...")
    print("-" * 70)
    
    results = model.train(**train_args)
    
    # Save best model
    best_model_path = project_dir / 'best.pt'
    model.export(format='onnx', opset=17)
    
    print()
    print("=" * 70)
    print("Training Complete!")
    print("=" * 70)
    print()
    print(f"Best model saved to: {best_model_path}")
    print(f"Training plots saved to: {project_dir}")
    print()
    
    # Print metrics
    metrics = model.val()
    print()
    print("Validation Metrics:")
    print(f"  mAP@50: {metrics.box.map50 * 100:.1f}%")
    print(f"  mAP@50-95: {metrics.box.map * 100:.1f}%")
    print(f"  Precision: {metrics.box.mp * 100:.1f}%")
    print(f"  Recall: {metrics.box.mr * 100:.1f}%")
    print()
    
    return results


def main():
    args = parse_args()
    config = load_config()
    
    # Override config with args
    config['training']['epochs'] = args.epochs
    config['training']['batch_size'] = args.batch_size
    config['model']['input_size'] = args.imgsz
    
    # Train
    results = train(args, config)
    
    print("✓ Training finished successfully!")


if __name__ == '__main__':
    main()
