"""
Model Export Script for Doctor Doom ML Models
==============================================

Exports trained PyTorch models to ONNX and CoreML formats for deployment.

Usage:
    python export_models.py --models-dir ./models --output-dir ./models

Supported formats:
    - ONNX (.onnx) - Cross-platform inference
    - CoreML (.mlmodel / .mlpackage) - Apple Silicon (Mac M2)
    - TorchScript (.pt) - PyTorch native
"""
import os
import sys
import argparse
import torch
from pathlib import Path
from typing import Dict, Tuple, Optional
import json

# Add models directory to path
sys.path.insert(0, str(Path(__file__).parent / 'models'))

from architectures import (
    Stage1HotspotDetector,
    Stage2CellAnalyzer,
    Stage3DefectClassifier,
    Stage4SeverityScorer,
    DoctorDoomPipeline,
    count_parameters
)


class ModelExporter:
    """Export trained models to various formats."""
    
    def __init__(self, models_dir: Path, output_dir: Path, device: str = 'cpu'):
        self.models_dir = models_dir
        self.output_dir = output_dir
        self.device = torch.device(device)
        
        # Model configurations
        self.model_configs = {
            'stage1': {
                'class': Stage1HotspotDetector,
                'input_shape': (1, 1, 640, 512),
                'input_names': ['thermal_image'],
                'output_names': ['hotspot_probability'],
                'dynamic_axes': {
                    'thermal_image': {0: 'batch'},
                    'hotspot_probability': {0: 'batch'}
                }
            },
            'stage2': {
                'class': Stage2CellAnalyzer,
                'input_shape': (1, 1, 640, 512),
                'input_names': ['thermal_image'],
                'output_names': ['cell_masks', 'cell_features'],
                'dynamic_axes': {
                    'thermal_image': {0: 'batch'},
                    'cell_masks': {0: 'batch'},
                    'cell_features': {0: 'batch'}
                }
            },
            'stage3': {
                'class': Stage3DefectClassifier,
                'input_shape': (1, 60, 128),
                'input_names': ['cell_features'],
                'output_names': ['defect_probabilities'],
                'dynamic_axes': {
                    'cell_features': {0: 'batch'},
                    'defect_probabilities': {0: 'batch'}
                }
            },
            'stage4': {
                'class': Stage4SeverityScorer,
                'input_shape': None,  # Multiple inputs
                'input_names': ['defect_type', 'cell_features', 'metadata'],
                'output_names': ['severity_score', 'recommendations'],
            }
        }
        
    def load_checkpoint(self, stage: int) -> Optional[torch.nn.Module]:
        """Load trained checkpoint for a stage."""
        checkpoint_path = self.models_dir / f'stage{stage}' / 'best_model.pth'
        
        if not checkpoint_path.exists():
            print(f"  ⚠ No checkpoint found at {checkpoint_path}")
            return None
        
        model = self.model_configs[f'stage{stage}']['class']().to(self.device)
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
        
        print(f"  ✓ Loaded checkpoint from epoch {checkpoint.get('epoch', 'unknown')}")
        return model
    
    def export_to_onnx(
        self,
        model: torch.nn.Module,
        stage: str,
        output_path: Path
    ) -> bool:
        """Export model to ONNX format."""
        try:
            config = self.model_configs[stage]
            model.eval()
            
            # Create dummy input
            if config['input_shape']:
                dummy_inputs = (torch.randn(*config['input_shape']).to(self.device),)
            else:
                # Special handling for stage 4
                dummy_inputs = (
                    torch.tensor([0], dtype=torch.long).to(self.device),
                    torch.randn(1, 60, 128).to(self.device),
                    torch.randn(1, 4).to(self.device)
                )
            
            # Export
            torch.onnx.export(
                model,
                dummy_inputs,
                str(output_path),
                export_params=True,
                opset_version=14,
                do_constant_folding=True,
                input_names=config['input_names'],
                output_names=config['output_names'],
                dynamic_axes=config.get('dynamic_axes', {})
            )
            
            file_size = output_path.stat().st_size / (1024 * 1024)  # MB
            print(f"  ✓ ONNX export complete: {output_path.name} ({file_size:.2f} MB)")
            return True
            
        except Exception as e:
            print(f"  ✗ ONNX export failed: {e}")
            return False
    
    def export_to_coreml(
        self,
        model: torch.nn.Module,
        stage: str,
        output_path: Path
    ) -> bool:
        """Export model to CoreML format."""
        try:
            import coremltools as ct
        except ImportError:
            print("  ⚠ coremltools not installed, skipping CoreML export")
            return False
        
        try:
            model.eval()
            config = self.model_configs[stage]
            
            # Create dummy input
            if config['input_shape']:
                dummy_input = torch.randn(*config['input_shape'])
            else:
                # For multi-input models, use first input
                dummy_input = torch.randn(1, 60, 128)
            
            # Trace the model
            traced_model = torch.jit.trace(model, dummy_input)
            
            # Convert to CoreML
            mlmodel = ct.convert(
                traced_model,
                inputs=[ct.TensorType(shape=dummy_input.shape, name=config['input_names'][0])],
                outputs=[ct.TensorType(name=name) for name in config['output_names']]
            )
            
            # Save
            mlmodel.save(str(output_path))
            
            file_size = output_path.stat().st_size / (1024 * 1024)  # MB
            print(f"  ✓ CoreML export complete: {output_path.name} ({file_size:.2f} MB)")
            return True
            
        except Exception as e:
            print(f"  ✗ CoreML export failed: {e}")
            return False
    
    def export_to_torchscript(
        self,
        model: torch.nn.Module,
        stage: str,
        output_path: Path
    ) -> bool:
        """Export model to TorchScript format."""
        try:
            model.eval()
            config = self.model_configs[stage]
            
            # Create dummy input
            if config['input_shape']:
                dummy_input = torch.randn(*config['input_shape'])
            else:
                dummy_input = (
                    torch.tensor([0], dtype=torch.long),
                    torch.randn(1, 60, 128),
                    torch.randn(1, 4)
                )
            
            # Trace
            traced_model = torch.jit.trace(model, dummy_input)
            
            # Save
            traced_model.save(output_path)
            
            file_size = output_path.stat().st_size / (1024 * 1024)  # MB
            print(f"  ✓ TorchScript export complete: {output_path.name} ({file_size:.2f} MB)")
            return True
            
        except Exception as e:
            print(f"  ✗ TorchScript export failed: {e}")
            return False
    
    def export_all(
        self,
        stage: str,
        formats: list = ['onnx', 'coreml', 'torchscript']
    ) -> Dict[str, bool]:
        """Export a stage to all requested formats."""
        print(f"\nExporting {stage}...")
        
        # Load model
        stage_num = int(stage.replace('stage', ''))
        model = self.load_checkpoint(stage_num)
        
        if model is None:
            return {'success': False}
        
        results = {}
        stage_output_dir = self.output_dir / stage
        
        # Export to each format
        if 'onnx' in formats:
            onnx_path = stage_output_dir / 'model.onnx'
            results['onnx'] = self.export_to_onnx(model, stage, onnx_path)
        
        if 'coreml' in formats:
            coreml_path = stage_output_dir / 'model.mlpackage'
            results['coreml'] = self.export_to_coreml(model, stage, coreml_path)
        
        if 'torchscript' in formats:
            ts_path = stage_output_dir / 'model.pt'
            results['torchscript'] = self.export_to_torchscript(model, stage, ts_path)
        
        return results


def export_pipeline(models_dir: Path, output_dir: Path, device: str = 'cpu'):
    """Export complete pipeline as a single model."""
    print("\n" + "="*60)
    print("Exporting Complete Pipeline")
    print("="*60)
    
    try:
        # Load all stage checkpoints
        pipeline = DoctorDoomPipeline().to(device)
        
        # Try to load checkpoints for each stage
        for stage_num in range(1, 5):
            checkpoint_path = models_dir / f'stage{stage_num}' / 'best_model.pth'
            if checkpoint_path.exists():
                checkpoint = torch.load(checkpoint_path, map_location=device)
                
                if stage_num == 1:
                    pipeline.stage1.load_state_dict(checkpoint['model_state_dict'])
                elif stage_num == 2:
                    pipeline.stage2.load_state_dict(checkpoint['model_state_dict'])
                elif stage_num == 3:
                    pipeline.stage3.load_state_dict(checkpoint['model_state_dict'])
                elif stage_num == 4:
                    pipeline.stage4.load_state_dict(checkpoint['model_state_dict'])
                
                print(f"  ✓ Loaded stage {stage_num} weights")
        
        pipeline.eval()
        
        # Export pipeline
        dummy_image = torch.randn(1, 1, 640, 512).to(device)
        dummy_metadata = torch.randn(1, 4).to(device)
        
        # TorchScript
        traced_pipeline = torch.jit.trace(pipeline, (dummy_image, dummy_metadata))
        pipeline_path = output_dir / 'pipeline.pt'
        traced_pipeline.save(pipeline_path)
        
        file_size = pipeline_path.stat().st_size / (1024 * 1024)
        print(f"\n  ✓ Pipeline exported: pipeline.pt ({file_size:.2f} MB)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Pipeline export failed: {e}")
        return False


def create_model_registry(output_dir: Path, export_results: Dict):
    """Create/update model registry after export."""
    registry_path = output_dir / 'registry.json'
    
    registry = {
        'export_date': torch.__version__,
        'stages': {}
    }
    
    for stage in ['stage1', 'stage2', 'stage3', 'stage4']:
        stage_dir = output_dir / stage
        if stage_dir.exists():
            files = list(stage_dir.glob('model.*'))
            registry['stages'][stage] = {
                'formats': [f.suffix for f in files],
                'exported': export_results.get(stage, {}).get('success', False)
            }
    
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"\n✓ Model registry saved to: {registry_path}")


def main():
    parser = argparse.ArgumentParser(description='Export Doctor Doom ML models')
    parser.add_argument('--models-dir', type=str, default='./models',
                       help='Directory with trained checkpoints')
    parser.add_argument('--output-dir', type=str, default='./models',
                       help='Output directory for exported models')
    parser.add_argument('--formats', type=str, nargs='+',
                       default=['onnx', 'coreml', 'torchscript'],
                       help='Export formats')
    parser.add_argument('--device', type=str, default='cpu',
                       help='Device for export (cpu/cuda)')
    parser.add_argument('--pipeline', action='store_true',
                       help='Also export complete pipeline')
    args = parser.parse_args()
    
    models_dir = Path(args.models_dir)
    output_dir = Path(args.output_dir)
    
    # Ensure output directories exist
    for stage in range(1, 5):
        (output_dir / f'stage{stage}').mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("Doctor Doom Model Exporter")
    print("="*60)
    print(f"\nModels directory: {models_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Export formats: {args.formats}")
    print(f"Device: {args.device}")
    
    # Create exporter
    exporter = ModelExporter(models_dir, output_dir, args.device)
    
    # Export each stage
    all_results = {}
    for stage in ['stage1', 'stage2', 'stage3', 'stage4']:
        results = exporter.export_all(stage, args.formats)
        results['success'] = any(results.values())
        all_results[stage] = results
    
    # Export complete pipeline if requested
    if args.pipeline:
        export_pipeline(models_dir, output_dir, args.device)
    
    # Create registry
    create_model_registry(output_dir, all_results)
    
    # Summary
    print("\n" + "="*60)
    print("Export Summary")
    print("="*60)
    
    for stage, results in all_results.items():
        status = "✓" if results.get('success', False) else "✗"
        formats = [k for k, v in results.items() if v and k != 'success']
        print(f"{status} {stage}: {', '.join(formats) if formats else 'None'}")
    
    print("\nExport complete!")


if __name__ == '__main__':
    main()
