#!/usr/bin/env python3
"""
ML Models Setup Script
======================

Download and setup all ML models for the Doctor Doom pipeline.

Usage:
    python setup_models.py [--source local|s3|http] [--model-dir /app/models]
"""
import argparse
import json
import os
from pathlib import Path
from typing import Dict, Optional

from model_manager import ModelManager, ModelInfo, ModelDownloader, setup_models


# Default model configurations
DEFAULT_MODELS = {
    'stage1': {
        'name': 'module-segmentation',
        'architecture': 'YOLOv8n-seg',
        'input': '640x512x1',
        'output': 'module masks + bboxes',
        'metrics': {'mAP50': 0.962},
        'description': 'Solar module segmentation from thermal imagery'
    },
    'stage2': {
        'name': 'defect-detection',
        'architecture': 'YOLOv8m',
        'input': '128x128x1',
        'output': '12-class defect bboxes',
        'metrics': {'mAP50': 0.931},
        'description': 'Defect detection and classification'
    },
    'stage3': {
        'name': 'severity-scoring',
        'architecture': 'XGBoost',
        'input': '77-dim features',
        'output': '3-class severity',
        'metrics': {'F1': 0.952},
        'description': 'Defect severity scoring'
    },
    'stage4': {
        'name': 'anomaly-detection',
        'architecture': 'ConvAE + IsolationForest',
        'input': '96-dim features',
        'output': 'anomaly score',
        'metrics': {'AUROC': 0.884},
        'description': 'Novel defect detection'
    }
}


def download_models(
    source: str = 'local',
    model_dir: str = '/app/models',
    s3_bucket: Optional[str] = None,
    http_url: Optional[str] = None
) -> Dict[int, str]:
    """
    Download all models from specified source.
    
    Args:
        source: Source type ('local', 's3', 'http')
        model_dir: Target model directory
        s3_bucket: S3 bucket name (if source='s3')
        http_url: Base HTTP URL (if source='http')
    
    Returns:
        Dictionary mapping stage to model path
    """
    manager = ModelManager(model_dir)
    downloader = ModelDownloader(cache_dir=f"{model_dir}/cache")
    
    print("=" * 60)
    print("Doctor Doom ML Models Setup")
    print("=" * 60)
    print(f"Model directory: {model_dir}")
    print(f"Source: {source}")
    print()
    
    # Create directory structure
    for stage in range(1, 5):
        stage_dir = Path(model_dir) / f"stage{stage}"
        stage_dir.mkdir(parents=True, exist_ok=True)
    
    # Download each stage
    for stage_num, config in DEFAULT_MODELS.items():
        stage = int(stage_num.replace('stage', ''))
        print(f"\nSetting up Stage {stage}: {config['name']}")
        print("-" * 40)
        
        # Determine source path
        if source == 'local':
            # Look for models in common locations
            possible_paths = [
                Path(f"./models/stage{stage}/model.onnx"),
                Path(f"../models/stage{stage}/model.onnx"),
                Path(f"/opt/doctor-doom/models/stage{stage}/model.onnx"),
            ]
            
            source_path = None
            for path in possible_paths:
                if path.exists():
                    source_path = path
                    break
            
            if source_path is None:
                print(f"  ⚠ No local model found for stage {stage}")
                print(f"    Creating placeholder...")
                _create_placeholder(manager, stage, config)
                continue
            
            # Copy model
            output_path = Path(model_dir) / f"stage{stage}" / "model.onnx"
            downloader.copy_from_local(source_path, output_path)
            
        elif source == 's3':
            if not s3_bucket:
                print(f"  ✗ S3 bucket not specified")
                continue
            
            s3_uri = f"s3://{s3_bucket}/models/stage{stage}/model.onnx"
            output_path = Path(model_dir) / f"stage{stage}" / "model.onnx"
            
            try:
                downloader.download_from_s3(s3_uri, output_path)
            except Exception as e:
                print(f"  ✗ Failed to download: {e}")
                _create_placeholder(manager, stage, config)
                continue
                
        elif source == 'http':
            if not http_url:
                print(f"  ✗ HTTP URL not specified")
                continue
            
            url = f"{http_url}/models/stage{stage}/model.onnx"
            output_path = Path(model_dir) / f"stage{stage}" / "model.onnx"
            
            try:
                downloader.download_from_http(url, output_path)
            except Exception as e:
                print(f"  ✗ Failed to download: {e}")
                _create_placeholder(manager, stage, config)
                continue
        
        # Register model
        model_info = ModelInfo(
            name=config['name'],
            version='1.0.0',
            stage=stage,
            format='onnx',
            size_mb=output_path.stat().st_size / 1e6,
            sha256='',  # Will be computed by register_model
            created_at='',
            metrics=config['metrics'],
            description=config['description']
        )
        manager.register_model(model_info)
        print(f"  ✓ Model registered: {config['name']} v1.0.0")
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    
    # Print summary
    print("\nModel Summary:")
    for model in manager.list_models():
        status = "✓" if Path(model_dir) / f"stage{model.stage}" / f"model.{model.format}" in model_dir.glob(f"stage{model.stage}/*") else "⚠"
        print(f"  {status} Stage {model.stage}: {model.name} v{model.version} ({model.format}, {model.size_mb:.1f} MB)")
    
    return {m.stage: str(Path(model_dir) / f"stage{m.stage}" / f"model.{m.format}") 
            for m in manager.list_models()}


def _create_placeholder(manager: ModelManager, stage: int, config: Dict):
    """Create placeholder info file for missing model."""
    stage_dir = Path(manager.model_dir) / f"stage{stage}"
    info_file = stage_dir / "model_info.json"
    
    info = {
        'stage': stage,
        'name': config['name'],
        'status': 'missing',
        'message': 'Model not found. Please download or train.',
        'expected_formats': ['onnx', 'coreml'],
        'architecture': config['architecture'],
        'input': config['input'],
        'output': config['output'],
        'metrics': config['metrics']
    }
    
    with open(info_file, 'w') as f:
        json.dump(info, f, indent=2)


def verify_models(model_dir: str = '/app/models') -> bool:
    """
    Verify all models are present and valid.
    
    Returns:
        True if all models verified
    """
    manager = ModelManager(model_dir)
    all_valid = True
    
    print("\nVerifying models...")
    print("-" * 40)
    
    for stage in range(1, 5):
        model = manager.get_default_model(stage)
        if model is None:
            print(f"  ✗ Stage {stage}: No model registered")
            all_valid = False
            continue
        
        model_path = Path(model_dir) / f"stage{stage}" / f"model.{model.format}"
        
        if not model_path.exists():
            print(f"  ✗ Stage {stage}: Model file not found")
            all_valid = False
            continue
        
        # Verify size
        actual_size = model_path.stat().st_size / 1e6
        size_diff = abs(actual_size - model.size_mb)
        
        if size_diff > 1.0:  # Allow 1 MB tolerance
            print(f"  ⚠ Stage {stage}: Size mismatch (expected {model.size_mb:.1f} MB, got {actual_size:.1f} MB)")
        
        # Verify hash if available
        if model.sha256:
            from model_manager import compute_model_hash
            actual_hash = compute_model_hash(model_path)
            if actual_hash != model.sha256:
                print(f"  ✗ Stage {stage}: Hash mismatch")
                all_valid = False
                continue
        
        print(f"  ✓ Stage {stage}: {model.name} v{model.version} verified")
    
    return all_valid


def main():
    parser = argparse.ArgumentParser(description='Setup ML models for Doctor Doom')
    parser.add_argument('--source', choices=['local', 's3', 'http'], default='local',
                       help='Model source (default: local)')
    parser.add_argument('--model-dir', default='/app/models',
                       help='Model directory (default: /app/models)')
    parser.add_argument('--s3-bucket', help='S3 bucket name (for s3 source)')
    parser.add_argument('--http-url', help='Base HTTP URL (for http source)')
    parser.add_argument('--verify', action='store_true',
                       help='Verify models after setup')
    
    args = parser.parse_args()
    
    # Download/setup models
    model_paths = download_models(
        source=args.source,
        model_dir=args.model_dir,
        s3_bucket=args.s3_bucket,
        http_url=args.http_url
    )
    
    # Verify if requested
    if args.verify:
        if verify_models(args.model_dir):
            print("\n✓ All models verified successfully!")
        else:
            print("\n✗ Some models failed verification")
            exit(1)
    
    # Print usage instructions
    print("\nNext steps:")
    print("  1. Start the ML service: docker compose up -d ml-inference")
    print("  2. Check health: curl http://localhost:8001/health")
    print("  3. Run inference: curl -X POST http://localhost:8001/api/v1/infer -d '{...}'")


if __name__ == '__main__':
    main()
