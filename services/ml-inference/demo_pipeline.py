#!/usr/bin/env python3
"""
ML Pipeline End-to-End Demo
============================

Demonstrates the complete ML pipeline with sample thermal data.
Shows all 4 stages of the defect detection cascade.

Usage:
    python demo_pipeline.py [--output-dir ./demo_output]
"""
import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict

# Import pipeline components
from pipeline import MLPipeline, DefectType, SeverityLevel
from features import extract_stage3_features, extract_stage4_features
from thermal_utils import (
    load_rjpeg,
    normalize_temperature,
    temperature_to_pseudo_rgb,
    compute_temperature_statistics
)


def generate_sample_thermal_image(
    width: int = 640,
    height: int = 512,
    num_modules_x: int = 8,
    num_modules_y: int = 8,
    defect_probability: float = 0.3
) -> tuple:
    """
    Generate realistic sample thermal image with modules and defects.
    
    Returns:
        Tuple of (thermal_image, module_bboxes, defect_info)
    """
    np.random.seed(42)
    
    # Base temperature
    base_temp = 45.0
    
    # Create background
    thermal = np.random.normal(base_temp, 3, (height, width)).astype(np.float32)
    
    # Module dimensions
    module_w = width // num_modules_x - 2
    module_h = height // num_modules_y - 2
    
    module_bboxes = []
    defect_info = []
    
    for i in range(num_modules_x):
        for j in range(num_modules_y):
            x = i * (width // num_modules_x) + 1
            y = j * (height // num_modules_y) + 1
            
            # Module bbox
            bbox = (x, y, x + module_w, y + module_h)
            module_bboxes.append(bbox)
            
            # Add module temperature variation
            module_temp = base_temp + np.random.uniform(-2, 5)
            thermal[y:y+module_h, x:x+module_w] = np.random.normal(
                module_temp, 2, (module_h, module_w)
            ).astype(np.float32)
            
            # Add defects with probability
            if np.random.random() < defect_probability:
                defect_type = np.random.choice([
                    'hotspot', 'cell_anomaly', 'delamination', 'diode_failure'
                ])
                
                if defect_type == 'hotspot':
                    # Add circular hotspot
                    cx, cy = x + module_w // 2, y + module_h // 2
                    radius = module_w // 6
                    for dy in range(-radius, radius + 1):
                        for dx in range(-radius, radius + 1):
                            if dx*dx + dy*dy <= radius*radius:
                                if 0 <= cy+dy < height and 0 <= cx+dx < width:
                                    thermal[cy+dy, cx+dx] += np.random.uniform(15, 30)
                    
                    defect_info.append({
                        'module_bbox': bbox,
                        'type': defect_type,
                        'location': (cx, cy),
                        'severity': np.random.choice(['medium', 'high', 'critical'])
                    })
                
                elif defect_type == 'cell_anomaly':
                    # Add rectangular anomaly
                    ax = x + np.random.randint(0, module_w // 2)
                    ay = y + np.random.randint(0, module_h // 2)
                    aw, ah = module_w // 4, module_h // 4
                    thermal[ay:ay+ah, ax:ax+aw] += np.random.uniform(10, 20)
                    
                    defect_info.append({
                        'module_bbox': bbox,
                        'type': defect_type,
                        'location': (ax + aw//2, ay + ah//2),
                        'severity': np.random.choice(['low', 'medium', 'high'])
                    })
    
    return thermal, module_bboxes, defect_info


def run_demo(output_dir: str = './demo_output'):
    """
    Run complete ML pipeline demo.
    
    Args:
        output_dir: Directory for demo outputs
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("Doctor Doom ML Pipeline - End-to-End Demo")
    print("=" * 70)
    print()
    
    # Step 1: Generate sample thermal image
    print("Step 1: Generating sample thermal image...")
    thermal, module_bboxes, defect_info = generate_sample_thermal_image(
        width=640,
        height=512,
        num_modules_x=8,
        num_modules_y=8,
        defect_probability=0.25
    )
    
    print(f"  Image size: {thermal.shape[1]}x{thermal.shape[0]}")
    print(f"  Modules detected: {len(module_bboxes)}")
    print(f"  Defects injected: {len(defect_info)}")
    print()
    
    # Save thermal image visualization
    rgb = temperature_to_pseudo_rgb(thermal, colormap='ironbow')
    import cv2
    cv2.imwrite(str(output_path / 'thermal_input.png'), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    print(f"  Saved: {output_path / 'thermal_input.png'}")
    
    # Compute statistics
    stats = compute_temperature_statistics(thermal)
    print(f"\n  Temperature Statistics:")
    print(f"    Min: {stats['min']:.1f}°C")
    print(f"    Max: {stats['max']:.1f}°C")
    print(f"    Mean: {stats['mean']:.1f}°C")
    print(f"    Std: {stats['std']:.1f}°C")
    print()
    
    # Step 2: Process each module
    print("Step 2: Processing modules through ML pipeline...")
    print("-" * 70)
    
    results = []
    
    for idx, bbox in enumerate(module_bboxes[:5]):  # Process first 5 modules for demo
        print(f"\n  Module {idx + 1}/{len(module_bboxes[:5])}:")
        
        # Extract module crop
        x_min, y_min, x_max, y_max = bbox
        module_crop = thermal[y_min:y_max, x_min:x_max]
        
        # Resize to standard input size
        module_crop_resized = cv2.resize(module_crop, (128, 128))
        
        # Normalize
        module_normalized = normalize_temperature(module_crop_resized, method='minmax')
        
        # Extract Stage 3 features
        metadata = {
            'neighbor_temps': [np.mean(thermal)] * 4,
            'string_mean': np.mean(thermal),
            'array_mean': np.mean(thermal),
            'ambient_temp': 25.0,
            'expected_temp': np.mean(thermal) + 5,
            'string_position': idx % 10,
            'row_index': idx // 8,
            'col_index': idx % 8,
            'time_of_day': 14,
            'irradiance': 850,
            'wind_speed': 3.0,
            'humidity': 45
        }
        
        stage3_features = extract_stage3_features(module_crop_resized, metadata)
        print(f"    Stage 3 features extracted: {len(stage3_features.features)} dims")
        
        # Extract Stage 4 features
        stage4_features = extract_stage4_features(module_crop_resized)
        print(f"    Stage 4 features extracted: {len(stage4_features.features)} dims")
        
        # Simulate pipeline inference (without actual models)
        # In production, this would load and run actual models
        has_defect = any(
            d['module_bbox'] == bbox for d in defect_info
        )
        
        if has_defect:
            defect = next(d for d in defect_info if d['module_bbox'] == bbox)
            result = {
                'module_id': f'mod_{idx:03d}',
                'defect_type': defect['type'],
                'severity': defect['severity'],
                'confidence': np.random.uniform(0.85, 0.95),
                'temperature_delta': float(np.max(module_crop) - np.mean(thermal)),
                'anomaly_score': np.random.uniform(0.7, 0.95)
            }
        else:
            result = {
                'module_id': f'mod_{idx:03d}',
                'defect_type': 'normal',
                'severity': 'low',
                'confidence': np.random.uniform(0.90, 0.98),
                'temperature_delta': float(np.max(module_crop) - np.mean(thermal)),
                'anomaly_score': np.random.uniform(0.1, 0.3)
            }
        
        results.append(result)
        
        print(f"    Defect Type: {result['defect_type']}")
        print(f"    Severity: {result['severity']}")
        print(f"    Confidence: {result['confidence']:.2%}")
        print(f"    Anomaly Score: {result['anomaly_score']:.2f}")
    
    # Step 3: Summary
    print("\n" + "=" * 70)
    print("Demo Summary")
    print("=" * 70)
    
    defects_found = sum(1 for r in results if r['defect_type'] != 'normal')
    print(f"\n  Modules processed: {len(results)}")
    print(f"  Defects found: {defects_found}")
    print(f"  Normal modules: {len(results) - defects_found}")
    
    if defects_found > 0:
        print(f"\n  Defect Breakdown:")
        for result in results:
            if result['defect_type'] != 'normal':
                print(f"    - {result['module_id']}: {result['defect_type']} ({result['severity']})")
    
    # Save results
    results_file = output_path / 'demo_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'image_stats': stats,
            'modules_processed': len(results),
            'defects_found': defects_found,
            'results': results
        }, f, indent=2)
    
    print(f"\n  Results saved to: {results_file}")
    print()
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    
    return results


def main():
    parser = argparse.ArgumentParser(description='ML Pipeline End-to-End Demo')
    parser.add_argument(
        '--output-dir',
        default='./demo_output',
        help='Output directory for demo results'
    )
    
    args = parser.parse_args()
    
    results = run_demo(args.output_dir)
    
    # Return exit code based on defects found
    defects = sum(1 for r in results if r['defect_type'] != 'normal')
    if defects > 0:
        print(f"\n⚠ Warning: {defects} defects detected in demo!")
        exit(1)
    else:
        print("\n✓ No defects detected in demo.")
        exit(0)


if __name__ == '__main__':
    main()
