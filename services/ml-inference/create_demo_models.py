#!/usr/bin/env python3
"""
Create Demo ML Models for Doctor Doom
======================================

Generates simple demo models that produce realistic-looking outputs
for testing and demonstration purposes.

These are not trained models, but they demonstrate the pipeline works.
"""
import numpy as np
import json
from pathlib import Path
from datetime import datetime


def create_demo_model(stage: int, model_dir: Path):
    """Create a demo model for a stage."""
    stage_dir = model_dir / f'stage{stage}'
    stage_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple numpy array as a placeholder "trained" model
    # In reality, this would be the model weights
    if stage == 1:
        # Stage 1: Hotspot detector - simple threshold model
        model_data = {
            'type': 'demo',
            'threshold': 0.65,
            'weights': np.random.rand(10).astype(np.float32)
        }
    elif stage == 2:
        # Stage 2: Cell analyzer - cell layout model
        model_data = {
            'type': 'demo',
            'cell_rows': 6,
            'cell_cols': 10,
            'cell_positions': np.array([[r, c] for r in range(6) for c in range(10)])
        }
    elif stage == 3:
        # Stage 3: Defect classifier - uniform distribution
        model_data = {
            'type': 'demo',
            'defect_types': [
                'hotspot', 'cell_anomaly', 'delamination',
                'diode_failure', 'crack', 'soiling', 
                'discoloration', 'normal'
            ],
            'prior_probabilities': np.array([0.35, 0.25, 0.15, 0.10, 0.08, 0.04, 0.02, 0.01])
        }
    elif stage == 4:
        # Stage 4: Severity scorer - linear mapping
        model_data = {
            'type': 'demo',
            'severity_thresholds': [0.25, 0.50, 0.75],
            'severity_levels': ['low', 'medium', 'high', 'critical']
        }
    
    # Save model
    model_path = stage_dir / 'demo_model.npy'
    np.save(model_path, model_data, allow_pickle=True)
    
    # Save model info
    info = {
        'name': f'stage{stage}-demo-model',
        'version': '1.0.0-demo',
        'stage': stage,
        'format': 'npy',
        'size_mb': model_path.stat().st_size / (1024 * 1024),
        'created_at': datetime.now().isoformat(),
        'description': f'Demo model for stage {stage} - for testing only',
        'status': 'demo'
    }
    
    with open(stage_dir / 'model_info.json', 'w') as f:
        json.dump(info, f, indent=2)
    
    print(f"✓ Created demo model for Stage {stage}: {model_path.name}")
    return info


def main():
    print("="*60)
    print("Creating Demo ML Models for Doctor Doom")
    print("="*60)
    
    models_dir = Path('/app/models')
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Create demo models for all stages
    models = []
    for stage in range(1, 5):
        info = create_demo_model(stage, models_dir)
        models.append(info)
    
    # Create registry
    registry = {
        'models': models,
        'default_versions': {str(i): '1.0.0-demo' for i in range(1, 5)},
        'created_at': datetime.now().isoformat(),
        'status': 'demo'
    }
    
    with open(models_dir / 'registry.json', 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"\n✓ Created demo models in: {models_dir}")
    print("\nDemo models are ready for testing!")
    print("Note: These are placeholder models for demonstration only.")
    print("For production, train real models using train_models.py")


if __name__ == '__main__':
    main()
