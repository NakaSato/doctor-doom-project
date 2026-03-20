#!/usr/bin/env python3
"""
Setup ML Models for Demo
=========================

Creates placeholder models and registry for demo purposes.
In production, download actual trained models.
"""
import json
import hashlib
import numpy as np
from pathlib import Path
from datetime import datetime


def create_placeholder_model(stage: int, model_dir: str = './models'):
    """
    Create placeholder model file for demo.
    
    In production, this would download actual trained models.
    """
    stage_path = Path(model_dir) / f"stage{stage}"
    stage_path.mkdir(parents=True, exist_ok=True)
    
    # Create a simple numpy array as placeholder
    # This simulates model weights
    if stage == 1:
        # YOLOv8n-seg placeholder
        model_data = np.random.randn(1000, 32).astype(np.float32)
        model_format = 'npy'
    elif stage == 2:
        # YOLOv8m placeholder
        model_data = np.random.randn(2000, 64).astype(np.float32)
        model_format = 'npy'
    elif stage == 3:
        # XGBoost placeholder
        model_data = np.random.randn(500, 77).astype(np.float32)
        model_format = 'npy'
    else:
        # Autoencoder placeholder
        model_data = np.random.randn(800, 96).astype(np.float32)
        model_format = 'npy'
    
    # Save model
    model_path = stage_path / f"model.{model_format}"
    np.save(model_path, model_data)
    
    # Compute hash
    sha256_hash = hashlib.sha256()
    with open(model_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    # Create model info
    model_info = {
        'name': f'stage{stage}-model',
        'version': '1.0.0',
        'stage': stage,
        'format': model_format,
        'size_mb': round(model_path.stat().st_size / 1e6, 2),
        'sha256': sha256_hash.hexdigest(),
        'created_at': datetime.now().isoformat(),
        'metrics': {
            1: {'mAP50': 0.962},
            2: {'mAP50': 0.931},
            3: {'F1': 0.952},
            4: {'AUROC': 0.884}
        }.get(stage, {}),
        'description': f'Stage {stage} placeholder model for demo',
        'status': 'placeholder'
    }
    
    # Save model info
    info_path = stage_path / 'model_info.json'
    with open(info_path, 'w') as f:
        json.dump(model_info, f, indent=2)
    
    print(f"  ✓ Stage {stage}: Created placeholder model ({model_info['size_mb']:.2f} MB)")
    
    return model_info


def create_registry(models: list, model_dir: str = './models'):
    """Create model registry file."""
    registry = {
        'models': models,
        'default_versions': {
            '1': '1.0.0',
            '2': '1.0.0',
            '3': '1.0.0',
            '4': '1.0.0'
        },
        'created_at': datetime.now().isoformat()
    }
    
    registry_path = Path(model_dir) / 'registry.json'
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"\n  ✓ Registry created: {registry_path}")


def main():
    print("=" * 60)
    print("Setting up ML Models for Demo")
    print("=" * 60)
    print()
    
    models = []
    
    for stage in range(1, 5):
        model_info = create_placeholder_model(stage)
        models.append(model_info)
    
    create_registry(models)
    
    print()
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run demo: python demo_pipeline.py")
    print("  2. Run tests: pytest tests/ -v")
    print("  3. Start service: python main.py")
    print()


if __name__ == '__main__':
    main()
