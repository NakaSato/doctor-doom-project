#!/usr/bin/env python3
"""
Generate Sample Thermal Images for Testing
==========================================

Creates realistic sample thermal images for testing the ML pipeline.
Generates images with various defect types and conditions.

Usage:
    uv run python scripts/generate_sample_images.py --output-dir ./sample_data
"""
import argparse
import json
import numpy as np
import cv2
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


def create_base_thermal_image(
    width: int = 640,
    height: int = 512,
    base_temp: float = 45.0,
    noise_std: float = 3.0
) -> np.ndarray:
    """Create base thermal image with realistic noise."""
    image = np.random.normal(base_temp, noise_std, (height, width)).astype(np.float32)
    
    # Add slight gradient (temperature variation across image)
    gradient = np.linspace(0, 2, width).reshape(1, -1)
    image = image + gradient
    
    return image


def add_module_pattern(
    image: np.ndarray,
    num_modules_x: int = 8,
    num_modules_y: int = 8,
    module_temp_offset: float = 5.0
) -> Tuple[np.ndarray, List[Dict]]:
    """Add solar module pattern to thermal image."""
    height, width = image.shape
    module_w = width // num_modules_x - 2
    module_h = height // num_modules_y - 2
    
    modules = []
    
    for i in range(num_modules_x):
        for j in range(num_modules_y):
            x = i * (width // num_modules_x) + 1
            y = j * (height // num_modules_y) + 1
            
            # Module bbox
            bbox = (x, y, x + module_w, y + module_h)
            
            # Add module temperature variation
            module_temp = module_temp_offset + np.random.uniform(-2, 2)
            image[y:y+module_h, x:x+module_w] += module_temp
            
            modules.append({
                "id": f"mod_{j:02d}_{i:02d}",
                "bbox": bbox,
                "row": j,
                "col": i,
                "base_temp": float(module_temp)
            })
    
    return image, modules


def add_hotspot(
    image: np.ndarray,
    center: Tuple[int, int],
    radius: int = 20,
    intensity: float = 25.0
) -> Dict:
    """Add circular hotspot defect."""
    cx, cy = center
    
    # Create gaussian hotspot
    y, x = np.ogrid[:image.shape[0], :image.shape[1]]
    mask = ((x - cx)**2 + **(y - cy)2) <= radius**2
    
    # Add temperature increase with gaussian falloff
    falloff = np.exp(-((x - cx)**2 + **(y - cy)2) / (2 * radius**2))
    image[mask] += intensity * falloff[0, mask[0]]
    
    return {
        "type": "hotspot",
        "center": center,
        "radius": radius,
        "intensity": intensity,
        "severity": "critical" if intensity > 20 else "high" if intensity > 15 else "medium"
    }


def add_cell_anomaly(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    intensity: float = 15.0
) -> Dict:
    """Add rectangular cell anomaly."""
    x1, y1, x2, y2 = bbox
    image[y1:y2, x1:x2] += intensity
    
    return {
        "type": "cell_anomaly",
        "bbox": bbox,
        "intensity": intensity,
        "severity": "high" if intensity > 12 else "medium"
    }


def add_delamination(
    image: np.ndarray,
    center: Tuple[int, int],
    size: Tuple[int, int] = (40, 30),
    intensity: float = 10.0
) -> Dict:
    """Add irregular delamination pattern."""
    cx, cy = center
    w, h = size
    
    # Create irregular shape
    y, x = np.ogrid[:image.shape[0], :image.shape[1]]
    mask = (np.abs(x - cx) / w + np.abs(y - cy) / h) <= 1
    
    # Add noise to edges
    image[cy-h//2:cy+h//2, cx-w//2:cx+w//2] += intensity * mask[cy-h//2:cy+h//2, cx-w//2:cx+w//2]
    
    return {
        "type": "delamination",
        "center": center,
        "size": size,
        "intensity": intensity,
        "severity": "medium"
    }


def add_diode_failure(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    intensity: float = 20.0
) -> Dict:
    """Add diode failure pattern (affects entire substring)."""
    x1, y1, x2, y2 = bbox
    
    # Affects larger area uniformly
    image[y1:y2, x1:x2] += intensity
    
    # Add hot border
    border = 5
    image[y1:y1+border, x1:x2] += intensity * 0.5
    image[y2-border:y2, x1:x2] += intensity * 0.5
    
    return {
        "type": "diode_failure",
        "bbox": bbox,
        "intensity": intensity,
        "severity": "critical"
    }


def generate_sample_image(
    seed: int = 42,
    width: int = 640,
    height: int = 512,
    defect_probability: float = 0.3
) -> Dict:
    """Generate complete sample thermal image with defects."""
    np.random.seed(seed)
    
    # Create base image
    image = create_base_thermal_image(width, height)
    
    # Add module pattern
    image, modules = add_module_pattern(image)
    
    # Add random defects
    defects = []
    defect_id = 0
    
    for module in modules:
        if np.random.random() < defect_probability:
            defect_type = np.random.choice([
                'hotspot', 'cell_anomaly', 'delamination', 'diode_failure'
            ])
            
            x1, y1, x2, y2 = module['bbox']
            module_center = ((x1 + x2) // 2, (y1 + y2) // 2)
            
            if defect_type == 'hotspot':
                defect = add_hotspot(
                    image,
                    center=(
                        module_center[0] + np.random.randint(-20, 20),
                        module_center[1] + np.random.randint(-20, 20)
                    ),
                    intensity=np.random.uniform(15, 30)
                )
            elif defect_type == 'cell_anomaly':
                cell_w = (x2 - x1) // 5
                cell_h = (y2 - y1) // 6
                cell_x = x1 + np.random.randint(0, 5) * cell_w
                cell_y = y1 + np.random.randint(0, 6) * cell_h
                
                defect = add_cell_anomaly(
                    image,
                    bbox=(cell_x, cell_y, cell_x + cell_w, cell_y + cell_h),
                    intensity=np.random.uniform(10, 20)
                )
            elif defect_type == 'delamination':
                defect = add_delamination(
                    image,
                    center=module_center,
                    size=(np.random.randint(30, 50), np.random.randint(20, 40)),
                    intensity=np.random.uniform(8, 15)
                )
            else:  # diode_failure
                # Affects 1/3 of module (one substring)
                third_h = (y2 - y1) // 3
                substring_y = y1 + np.random.randint(0, 3) * third_h
                
                defect = add_diode_failure(
                    image,
                    bbox=(x1, substring_y, x2, substring_y + third_h),
                    intensity=np.random.uniform(15, 25)
                )
            
            defect['id'] = f"defect_{defect_id:03d}"
            defect['module_id'] = module['id']
            defects.append(defect)
            defect_id += 1
    
    return {
        "image": image,
        "modules": modules,
        "defects": defects,
        "metadata": {
            "width": width,
            "height": height,
            "base_temp": 45.0,
            "defect_count": len(defects),
            "generated_at": datetime.now().isoformat(),
            "seed": seed
        }
    }


def save_sample_data(
    sample_data: Dict,
    output_dir: str,
    prefix: str = "sample"
):
    """Save sample thermal image and metadata."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    image = sample_data['image']
    
    # Save temperature data (numpy)
    np.save(output_path / f"{prefix}_temperature.npy", image)
    
    # Save visualization (pseudo-RGB)
    normalized = (image - image.min()) / (image.max() - image.min())
    rgb = cv2.applyColorMap((normalized * 255).astype(np.uint8), cv2.COLORMAP_HOT)
    cv2.imwrite(str(output_path / f"{prefix}_thermal.png"), rgb)
    
    # Save metadata
    metadata = {
        "modules": sample_data['modules'],
        "defects": sample_data['defects'],
        "metadata": sample_data['metadata']
    }
    
    with open(output_path / f"{prefix}_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Saved to {output_path}:")
    print(f"  - {prefix}_temperature.npy ({image.shape}, {image.dtype})")
    print(f"  - {prefix}_thermal.png (visualization)")
    print(f"  - {prefix}_metadata.json (modules + defects)")


def main():
    parser = argparse.ArgumentParser(description='Generate sample thermal images')
    parser.add_argument('--output-dir', default='./sample_data',
                       help='Output directory')
    parser.add_argument('--num-samples', type=int, default=5,
                       help='Number of samples to generate')
    parser.add_argument('--width', type=int, default=640,
                       help='Image width')
    parser.add_argument('--height', type=int, default=512,
                       help='Image height')
    parser.add_argument('--defect-prob', type=float, default=0.3,
                       help='Probability of defect per module')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Generating Sample Thermal Images")
    print("=" * 60)
    print()
    
    for i in range(args.num_samples):
        print(f"Generating sample {i+1}/{args.num_samples}...")
        
        sample = generate_sample_image(
            seed=i,
            width=args.width,
            height=args.height,
            defect_probability=args.defect_prob
        )
        
        save_sample_data(sample, args.output_dir, f"sample_{i:03d}")
        
        print(f"  Modules: {len(sample['modules'])}")
        print(f"  Defects: {len(sample['defects'])}")
        print()
    
    print("=" * 60)
    print(f"Generation complete! Output: {args.output_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()
