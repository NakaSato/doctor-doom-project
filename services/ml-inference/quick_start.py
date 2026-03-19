#!/usr/bin/env python3
"""
Quick Start Guide for Doctor Doom ML Models
============================================

This script helps you quickly train and export models for the Doctor Doom project.

Usage:
    # Quick training with default settings (5 epochs, 1000 samples)
    python quick_start.py

    # Full training (50 epochs, 10000 samples)
    python quick_start.py --full

    # Only export existing models
    python quick_start.py --export-only

    # Test inference with trained models
    python quick_start.py --test
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    print("\n" + "="*60)
    print("Checking Dependencies")
    print("="*60)
    
    required = {
        'torch': 'PyTorch',
        'numpy': 'NumPy',
        'tqdm': 'tqdm',
    }
    
    missing = []
    
    for package, name in required.items():
        try:
            __import__(package)
            print(f"✓ {name} installed")
        except ImportError:
            print(f"✗ {name} NOT installed")
            missing.append(name)
    
    # Optional but recommended
    print("\nOptional packages:")
    optional = {
        'onnxruntime': 'ONNX Runtime',
        'onnx': 'ONNX',
        'coremltools': 'CoreML Tools (macOS only)',
        'opencv_python': 'OpenCV',
    }
    
    for package, name in optional.items():
        try:
            __import__(package.replace('_', '-'))
            print(f"✓ {name} installed")
        except ImportError:
            print(f"⚠ {name} NOT installed (optional)")
    
    if missing:
        print(f"\n❌ Missing required packages: {', '.join(missing)}")
        print("\nInstall with:")
        print("  pip install torch numpy tqdm")
        return False
    
    print("\n✓ All required dependencies found")
    return True


def train_models(quick: bool = True) -> bool:
    """Run model training."""
    cmd = [sys.executable, 'train_models.py']
    
    if quick:
        cmd.extend([
            '--epochs', '5',
            '--batch-size', '16',
            '--num-samples', '1000'
        ])
        description = "Training Models (Quick Mode - 5 epochs, 1000 samples)"
    else:
        cmd.extend([
            '--epochs', '50',
            '--batch-size', '32',
            '--num-samples', '10000'
        ])
        description = "Training Models (Full Mode - 50 epochs, 10000 samples)"
    
    return run_command(cmd, description)


def export_models() -> bool:
    """Export trained models to ONNX and CoreML."""
    cmd = [
        sys.executable, 'export_models.py',
        '--models-dir', './models',
        '--output-dir', './models',
        '--formats', 'onnx', 'torchscript'
    ]
    
    # Try to add CoreML if on macOS
    if sys.platform == 'darwin':
        cmd.append('coreml')
    
    return run_command(cmd, "Exporting Models to ONNX/CoreML")


def test_inference() -> bool:
    """Test inference with trained models."""
    cmd = [sys.executable, 'test_inference.py']
    return run_command(cmd, "Testing Inference")


def main():
    parser = argparse.ArgumentParser(
        description='Quick Start for Doctor Doom ML Models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--full', action='store_true',
                       help='Run full training (50 epochs, 10000 samples)')
    parser.add_argument('--export-only', action='store_true',
                       help='Only export existing models (skip training)')
    parser.add_argument('--test', action='store_true',
                       help='Test inference after training/export')
    parser.add_argument('--skip-checks', action='store_true',
                       help='Skip dependency checks')
    
    args = parser.parse_args()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("\n" + "="*60)
    print("Doctor Doom ML Models - Quick Start")
    print("="*60)
    
    # Check dependencies
    if not args.skip_checks and not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        sys.exit(1)
    
    # Training
    if not args.export_only:
        success = train_models(quick=not args.full)
        if not success:
            print("\n⚠ Training failed or was interrupted")
            print("You can still try to export any partially trained models")
    
    # Export
    export_models()
    
    # Test
    if args.test:
        test_inference()
    
    print("\n" + "="*60)
    print("Quick Start Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Check the ./models directory for trained models")
    print("2. Restart the ml-inference service to use new models:")
    print("   docker compose restart ml-inference")
    print("3. Test the service:")
    print("   curl http://localhost:8001/health")
    print("\nFor more information, see ML_ARCHITECTURE.md and TRAINING.md")


if __name__ == '__main__':
    main()
