#!/usr/bin/env python3
"""
Stage 1 Model Verification Script

Verifies the Stage 1 model setup, format, and readiness for inference.
"""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_stage1(model_dir: str = "models"):
    """Verify Stage 1 model setup."""
    print("=" * 70)
    print("Stage 1: Module Segmentation - Model Verification")
    print("=" * 70)
    
    model_path = Path(model_dir) / "stage1"
    issues = []
    warnings = []
    
    # Check 1: Directory exists
    print("\n[1/6] Checking directory structure...")
    if not model_path.exists():
        print(f"  ✗ FAIL: Directory not found: {model_path}")
        return False, ["Directory not found"]
    print(f"  ✓ Directory exists: {model_path}")
    
    # Check 2: List files
    print("\n[2/6] Checking model files...")
    files = list(model_path.glob("*"))
    if not files:
        print(f"  ✗ FAIL: No files found in {model_path}")
        return False, ["No model files found"]
    
    print(f"  Found {len(files)} file(s):")
    for f in files:
        size = f.stat().st_size / 1024  # KB
        print(f"    - {f.name} ({size:.1f} KB)")
    
    # Check 3: Model info
    print("\n[3/6] Checking model_info.json...")
    info_path = model_path / "model_info.json"
    model_info = {}
    if not info_path.exists():
        warnings.append("model_info.json not found")
        print(f"  ⚠ WARNING: model_info.json not found")
    else:
        with open(info_path) as f:
            model_info = json.load(f)
        print(f"  ✓ Model info loaded")
        print(f"    - Name: {model_info.get('name', 'N/A')}")
        print(f"    - Version: {model_info.get('version', 'N/A')}")
        print(f"    - Format: {model_info.get('format', 'N/A')}")
        print(f"    - Status: {model_info.get('status', 'N/A')}")
    
    # Check 4: Model format
    print("\n[4/6] Checking model format...")
    onnx_path = model_path / "model.onnx"
    coreml_path = model_path / "model_coreml.mlpackage"
    npy_path = model_path / "model.npy"
    
    formats_found = []
    has_production_model = False
    
    if onnx_path.exists():
        formats_found.append("ONNX")
        has_production_model = True
        print(f"  ✓ ONNX model found ({onnx_path.stat().st_size / 1024 / 1024:.2f} MB)")
    else:
        print(f"  ✗ ONNX model not found")
    
    if coreml_path.exists():
        formats_found.append("CoreML")
        has_production_model = True
        print(f"  ✓ CoreML model found")
    else:
        print(f"  ✗ CoreML model not found")
    
    if npy_path.exists():
        formats_found.append("NPY (placeholder)")
        print(f"  ⚠ NPY placeholder found ({npy_path.stat().st_size / 1024:.1f} KB)")
    
    if not formats_found:
        print(f"  ✗ FAIL: No model files found")
        return False, ["No model files found"]
    
    # Check 5: Model registry
    print("\n[5/6] Checking model registry...")
    registry_path = Path(model_dir) / "registry.json"
    if registry_path.exists():
        with open(registry_path) as f:
            registry = json.load(f)
        stage1_registered = any(
            m.get('stage') == 1 
            for m in registry.get('models', [])
        )
        if stage1_registered:
            print(f"  ✓ Stage 1 registered in registry.json")
        else:
            warnings.append("Stage 1 not in registry.json")
            print(f"  ⚠ WARNING: Stage 1 not in registry.json")
    else:
        print(f"  ⚠ WARNING: registry.json not found")
    
    # Check 6: Try to load ONNX model
    print("\n[6/6] Testing model loading...")
    model_loadable = False
    
    if onnx_path.exists():
        try:
            import onnxruntime as ort
            session = ort.InferenceSession(str(onnx_path))
            print(f"  ✓ ONNX model loads successfully")
            print(f"    - Inputs: {[i.name for i in session.get_inputs()]}")
            print(f"    - Outputs: {[o.name for o in session.get_outputs()]}")
            model_loadable = True
        except Exception as e:
            issues.append(f"ONNX load error: {e}")
            print(f"  ✗ FAIL: Error loading ONNX model: {e}")
    elif npy_path.exists():
        print(f"  ℹ Placeholder model (NPY format)")
        print(f"    - Cannot test inference with placeholder")
        print(f"    - Train real model for production use")
        model_loadable = False
    else:
        issues.append("No loadable model format found")
        print(f"  ✗ FAIL: No loadable model found")
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    is_placeholder = model_info.get('status') == 'placeholder'
    
    if is_placeholder:
        print("\n📋 Status: ⚠️  PLACEHOLDER MODEL")
        print("\n   This is a demo/placeholder model (NPY format).")
        print("\n   To deploy for production:")
        print("   ─────────────────────────")
        print("   1. Train model:")
        print("      python scripts/train_stage1.py \\")
        print("          --data datasets/processed/stage1 \\")
        print("          --epochs 200 \\")
        print("          --batch-size 32")
        print()
        print("   2. Export model:")
        print("      python scripts/export_models.py \\")
        print("          --input-dir runs/segment/stage1_segmentation/weights \\")
        print("          --output-dir models \\")
        print("          --formats onnx coreml")
        print()
        print("   3. Verify deployment:")
        print("      python scripts/verify_stage1.py")
    elif has_production_model and model_loadable:
        print("\n✅ Status: READY FOR INFERENCE")
    else:
        print("\n❌ Status: INCOMPLETE SETUP")
    
    print(f"\n📁 Model Directory: {model_path.absolute()}")
    print(f"📦 Formats Available: {', '.join(formats_found)}")
    
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"   - {w}")
    
    if issues:
        print(f"\n❌ Issues ({len(issues)}):")
        for i in issues:
            print(f"   - {i}")
    
    # Return status
    is_ready = has_production_model and model_loadable
    return is_ready, issues + warnings


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify Stage 1 model")
    parser.add_argument("--model-dir", type=str, default="models", help="Model directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    is_ready, messages = verify_stage1(args.model_dir)
    
    if args.json:
        result = {
            "stage": 1,
            "name": "module-segmentation",
            "ready": is_ready,
            "issues": messages,
        }
        print(json.dumps(result, indent=2))
    
    sys.exit(0 if is_ready else 1)
