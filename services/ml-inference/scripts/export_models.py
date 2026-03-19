#!/usr/bin/env python3
"""
Model Export Utility

Exports trained models to various formats (ONNX, CoreML, TensorRT).

Usage:
    python export_models.py --input-dir models/trained --output-dir models/exported --formats onnx coreml
"""
import argparse
import json
from pathlib import Path
import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description='Export ML models')
    parser.add_argument('--input-dir', type=str, required=True, help='Input directory with trained models')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory for exported models')
    parser.add_argument('--formats', nargs='+', default=['onnx', 'coreml'], help='Export formats')
    parser.add_argument('--quantize', action='store_true', help='Apply quantization')
    parser.add_argument('--precision', type=str, default='fp16', choices=['fp32', 'fp16', 'int8'], help='Precision')
    return parser.parse_args()


def export_stage1(input_dir, output_dir, formats, precision):
    """Export Stage 1: Module Segmentation (YOLOv8n-seg)."""
    print("\nExporting Stage 1: Module Segmentation...")
    
    try:
        from ultralytics import YOLO
        
        # Load model
        model_path = Path(input_dir) / 'stage1' / 'best.pt'
        if not model_path.exists():
            print(f"  ✗ Model not found: {model_path}")
            return
        
        model = YOLO(str(model_path))
        
        # Export to each format
        for fmt in formats:
            try:
                if fmt == 'onnx':
                    model.export(format='onnx', opset=17)
                    print(f"  ✓ ONNX exported")
                elif fmt == 'coreml':
                    model.export(format='coreml', precision=precision)
                    print(f"  ✓ CoreML ({precision}) exported")
            except Exception as e:
                print(f"  ✗ Failed to export {fmt}: {e}")
        
    except Exception as e:
        print(f"  ✗ Export failed: {e}")


def export_stage2(input_dir, output_dir, formats, precision):
    """Export Stage 2: Defect Detection (YOLOv8m)."""
    print("\nExporting Stage 2: Defect Detection...")
    
    try:
        from ultralytics import YOLO
        
        # Load model
        model_path = Path(input_dir) / 'stage2' / 'best.pt'
        if not model_path.exists():
            print(f"  ✗ Model not found: {model_path}")
            return
        
        model = YOLO(str(model_path))
        
        # Export to each format
        for fmt in formats:
            try:
                if fmt == 'onnx':
                    model.export(format='onnx', opset=17)
                    print(f"  ✓ ONNX exported")
                elif fmt == 'coreml':
                    model.export(format='coreml', precision=precision)
                    print(f"  ✓ CoreML ({precision}) exported")
            except Exception as e:
                print(f"  ✗ Failed to export {fmt}: {e}")
        
    except Exception as e:
        print(f"  ✗ Export failed: {e}")


def export_stage3(input_dir, output_dir, formats, precision):
    """Export Stage 3: Severity Scoring (XGBoost)."""
    print("\nExporting Stage 3: Severity Scoring...")
    
    try:
        import xgboost as xgb
        import onnxmltools
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        
        # Load model
        model_path = Path(input_dir) / 'stage3' / 'model.json'
        if not model_path.exists():
            print(f"  ✗ Model not found: {model_path}")
            return
        
        model = xgb.XGBClassifier()
        model.load_model(str(model_path))
        
        # Export to ONNX
        if 'onnx' in formats:
            try:
                # Convert to ONNX
                initial_type = [('float_input', FloatTensorType([None, 77]))]
                onnx_model = convert_sklearn(model, initial_types=initial_type)
                
                onnx_path = Path(output_dir) / 'stage3' / 'model.onnx'
                onnx_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(onnx_path, 'wb') as f:
                    f.write(onnx_model.SerializeToString())
                
                print(f"  ✓ ONNX exported")
            except Exception as e:
                print(f"  ✗ Failed to export ONNX: {e}")
        
    except Exception as e:
        print(f"  ✗ Export failed: {e}")


def export_stage4(input_dir, output_dir, formats, precision):
    """Export Stage 4: Anomaly Detection (ConvAE + IF)."""
    print("\nExporting Stage 4: Anomaly Detection...")
    
    try:
        import torch
        import joblib
        
        # Load Autoencoder
        ae_path = Path(input_dir) / 'stage4' / 'ae_final.pt'
        config_path = Path(input_dir) / 'stage4' / 'config.json'
        
        if not ae_path.exists():
            print(f"  ✗ Autoencoder not found: {ae_path}")
            return
        
        # Load config to get architecture
        with open(config_path) as f:
            config = json.load(f)
        
        # Recreate model
        from train_stage4 import ConvAutoencoder
        model = ConvAutoencoder(bottleneck_dim=config['bottleneck_dim'])
        model.load_state_dict(torch.load(ae_path, map_location='cpu'))
        model.eval()
        
        # Export to ONNX
        if 'onnx' in formats:
            try:
                dummy_input = torch.randn(1, 1, 128, 128)
                
                onnx_path = Path(output_dir) / 'stage4' / 'ae.onnx'
                onnx_path.parent.mkdir(parents=True, exist_ok=True)
                
                torch.onnx.export(
                    model.encoder,
                    dummy_input,
                    onnx_path,
                    export_params=True,
                    opset_version=17,
                    input_names=['input'],
                    output_names=['bottleneck'],
                )
                
                print(f"  ✓ ONNX (encoder) exported")
            except Exception as e:
                print(f"  ✗ Failed to export ONNX: {e}")
        
        # Export Isolation Forest
        if_path = Path(input_dir) / 'stage4' / 'isolation_forest.joblib'
        if if_path.exists():
            import shutil
            output_if_path = Path(output_dir) / 'stage4' / 'isolation_forest.joblib'
            output_if_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(if_path, output_if_path)
            print(f"  ✓ Isolation Forest copied")
        
    except Exception as e:
        print(f"  ✗ Export failed: {e}")


def main():
    args = parse_args()
    
    print("=" * 70)
    print("Model Export Utility")
    print("=" * 70)
    print()
    print(f"Input:  {args.input_dir}")
    print(f"Output: {args.output_dir}")
    print(f"Formats: {', '.join(args.formats)}")
    print(f"Precision: {args.precision}")
    print()
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Export each stage
    export_stage1(args.input_dir, args.output_dir, args.formats, args.precision)
    export_stage2(args.input_dir, args.output_dir, args.formats, args.precision)
    export_stage3(args.input_dir, args.output_dir, args.formats, args.precision)
    export_stage4(args.input_dir, args.output_dir, args.formats, args.precision)
    
    print()
    print("=" * 70)
    print("Export Complete!")
    print("=" * 70)
    print()
    print(f"Exported models saved to: {args.output_dir}")


if __name__ == '__main__':
    main()
