#!/usr/bin/env python3
"""
Test ML Pipeline with Real Thermal Images
==========================================

Tests the complete ML pipeline using real DJI and FLIR thermal images
from the tests/images dataset.

Usage:
    uv run python test_with_real_images.py --images-dir ./tests/images
"""
import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Import ML components
from thermal_utils import load_rjpeg, temperature_to_pseudo_rgb, compute_temperature_statistics
from features import extract_stage3_features, extract_stage4_features


def load_image_metadata(meta_file: Path) -> Dict[str, Any]:
    """Load metadata from .txt file or return empty dict."""
    metadata = {}
    
    if not meta_file.exists():
        return metadata
    
    try:
        with open(meta_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Try to convert to appropriate type
                    try:
                        if '.' in value:
                            metadata[key] = float(value)
                        else:
                            metadata[key] = int(value)
                    except ValueError:
                        metadata[key] = value
    except Exception as e:
        # File might be binary (Exif data)
        pass
    
    return metadata


def test_thermal_parser_with_images(images_dir: str):
    """Test thermal_parser with real thermal images."""
    images_path = Path(images_dir)
    
    print("=" * 70)
    print("Testing thermal_parser with Real Thermal Images")
    print("=" * 70)
    print()
    
    # Find all JPG files
    jpg_files = list(images_path.glob("*.jpg")) + list(images_path.glob("*.JPG"))
    
    if not jpg_files:
        print(f"No JPG files found in {images_path}")
        return
    
    print(f"Found {len(jpg_files)} thermal images")
    print()
    
    results = []
    
    for jpg_file in jpg_files:
        print(f"Processing: {jpg_file.name}")
        print("-" * 50)
        
        # Check for metadata file
        meta_file = jpg_file.with_suffix('.txt')
        metadata = load_image_metadata(meta_file)
        
        try:
            # Load thermal image
            thermal_image = load_rjpeg(jpg_file)
            
            print(f"  ✓ Loaded: {thermal_image.width}x{thermal_image.height}")
            print(f"  Temperature range: {thermal_image.min_temp:.1f}°C - {thermal_image.max_temp:.1f}°C")
            print(f"  Mean temp: {thermal_image.mean_temp:.1f}°C")
            
            # Compute statistics
            stats = compute_temperature_statistics(thermal_image.temperature)
            
            print(f"  Statistics:")
            print(f"    Std: {stats['std']:.2f}°C")
            print(f"    Skewness: {stats['skewness']:.3f}")
            print(f"    P95: {stats['p95']:.1f}°C")
            
            # Save visualization
            output_dir = images_path.parent / "test_output" / jpg_file.stem
            output_dir.mkdir(parents=True, exist_ok=True)
            
            rgb = temperature_to_pseudo_rgb(thermal_image.temperature, colormap='ironbow')
            import cv2
            cv2.imwrite(str(output_dir / "thermal.png"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
            
            # Save temperature data
            np.save(output_dir / "temperature.npy", thermal_image.temperature)
            
            # Save metadata
            result = {
                'file': jpg_file.name,
                'width': thermal_image.width,
                'height': thermal_image.height,
                'min_temp': thermal_image.min_temp,
                'max_temp': thermal_image.max_temp,
                'mean_temp': thermal_image.mean_temp,
                'statistics': stats,
                'metadata': metadata,
                'timestamp': datetime.now().isoformat(),
                'output_dir': str(output_dir)
            }
            
            with open(output_dir / "analysis.json", 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"  ✓ Saved to: {output_dir}")
            results.append(result)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                'file': jpg_file.name,
                'error': str(e)
            })
        
        print()
    
    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    
    successful = sum(1 for r in results if 'error' not in r)
    failed = len(results) - successful
    
    print(f"  Total images: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    
    if successful > 0:
        avg_temp = np.mean([r['mean_temp'] for r in results if 'error' not in r])
        avg_max = np.mean([r['max_temp'] for r in results if 'error' not in r])
        print(f"  Average mean temp: {avg_temp:.1f}°C")
        print(f"  Average max temp: {avg_max:.1f}°C")
    
    print()
    
    # Save summary
    summary = {
        'total_images': len(results),
        'successful': successful,
        'failed': failed,
        'results': results,
        'timestamp': datetime.now().isoformat()
    }
    
    summary_file = images_path.parent / "test_output" / "test_summary.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary saved to: {summary_file}")
    print("=" * 70)
    
    return results


def test_feature_extraction(images_dir: str):
    """Test feature extraction with real thermal images."""
    images_path = Path(images_dir)
    output_dir = images_path.parent / "test_output" / "features"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print()
    print("=" * 70)
    print("Testing Feature Extraction")
    print("=" * 70)
    print()
    
    # Find processed images
    feature_results = []
    
    for npy_file in (images_path.parent / "test_output").rglob("temperature.npy"):
        print(f"Processing: {npy_file.parent.name}")
        
        try:
            # Load temperature data
            temperature = np.load(npy_file)
            
            # Resize to 128x128 for module crop simulation
            import cv2
            crop = cv2.resize(temperature, (128, 128))
            
            # Extract Stage 3 features
            metadata = {
                'neighbor_temps': [float(np.mean(crop))] * 4,
                'string_mean': float(np.mean(crop)),
                'array_mean': float(np.mean(crop)),
                'ambient_temp': 25.0,
                'expected_temp': float(np.mean(crop)) + 5,
                'string_position': 1,
                'row_index': 0,
                'col_index': 0,
                'time_of_day': 12,
                'irradiance': 800,
                'wind_speed': 2.0,
                'humidity': 50
            }
            
            stage3_result = extract_stage3_features(crop, metadata)
            stage4_result = extract_stage4_features(crop)
            
            print(f"  Stage 3 features: {stage3_result.features.shape}")
            print(f"  Stage 4 features: {stage4_result.features.shape}")
            
            # Save features
            feature_data = {
                'source': npy_file.parent.name,
                'stage3_features': stage3_result.features.tolist(),
                'stage3_names': stage3_result.feature_names,
                'stage4_features': stage4_result.features.tolist(),
                'stage4_names': stage4_result.feature_names,
                'statistics': {
                    'mean': float(np.mean(crop)),
                    'std': float(np.std(crop)),
                    'min': float(np.min(crop)),
                    'max': float(np.max(crop))
                }
            }
            
            feature_file = output_dir / f"{npy_file.parent.name}_features.json"
            with open(feature_file, 'w') as f:
                json.dump(feature_data, f, indent=2)
            
            print(f"  ✓ Saved: {feature_file}")
            feature_results.append(feature_data)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print()
    
    # Summary
    print("=" * 70)
    print(f"Feature extraction complete: {len(feature_results)} samples")
    print(f"Output: {output_dir}")
    print("=" * 70)
    
    return feature_results


def main():
    parser = argparse.ArgumentParser(description='Test ML pipeline with real thermal images')
    parser.add_argument('--images-dir', default='./tests/images',
                       help='Directory containing thermal images')
    parser.add_argument('--test-parser', action='store_true', default=True,
                       help='Test thermal_parser')
    parser.add_argument('--test-features', action='store_true', default=True,
                       help='Test feature extraction')
    
    args = parser.parse_args()
    
    results = {}
    
    if args.test_parser:
        parser_results = test_thermal_parser_with_images(args.images_dir)
        results['parser'] = parser_results
    
    if args.test_features:
        feature_results = test_feature_extraction(args.images_dir)
        results['features'] = feature_results
    
    # Final summary
    print()
    print("=" * 70)
    print("All Tests Complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Review test_output/ directory for results")
    print("  2. Check thermal.png visualizations")
    print("  3. Analyze feature distributions in features/*.json")
    print()


if __name__ == '__main__':
    main()
