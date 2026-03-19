#!/usr/bin/env python3
"""
Test ML Inference with Demo Data
=================================
"""
import requests
import numpy as np
import base64
import json

# Generate demo thermal image (640x512 float32 array)
def generate_demo_thermal_image() -> str:
    """Generate a synthetic thermal image and return as base64."""
    # Create base temperature pattern
    image = np.ones((640, 512), dtype=np.float32) * 35.0  # Base 35°C
    
    # Add some cell-like patterns
    cell_height = 512 // 6
    cell_width = 640 // 10
    
    for row in range(6):
        for col in range(10):
            y1, y2 = row * cell_height, (row + 1) * cell_height
            x1, x2 = col * cell_width, (col + 1) * cell_width
            
            # Add slight variation per cell
            variation = np.random.uniform(-2, 2)
            image[y1:y2, x1:x2] += variation
            
            # Add a hotspot in one cell
            if row == 2 and col == 3:
                cy, cx = (y1 + y2) // 2, (x1 + x2) // 2
                for y in range(y1, y2):
                    for x in range(x1, x2):
                        dist = np.sqrt((y - cy)**2 + (x - cx)**2)
                        if dist < 30:
                            image[y, x] += 25.0  # Hotspot!
    
    # Add some noise
    image += np.random.normal(0, 0.5, image.shape)
    
    # Convert to base64
    image_bytes = image.tobytes()
    return base64.b64encode(image_bytes).decode('utf-8')


def test_inference():
    """Test the ML inference endpoint."""
    url = "http://localhost:8001/api/v1/infer"
    
    # Generate demo thermal data
    thermal_data = generate_demo_thermal_image()
    
    # Prepare request
    payload = {
        "module_id": "mod_001_05",
        "inspection_id": "insp_001",
        "image_id": "img_demo_001",
        "thermal_data": thermal_data,
        "metadata": {
            "thermal": {
                "ambient_temperature": 25.0,
                "max_temperature": float(np.frombuffer(base64.b64decode(thermal_data), dtype=np.float32).max()),
                "temperature_delta": 25.0,
                "irradiance_w_m2": 850
            },
            "module": {
                "manufacturer": "SolarTech",
                "model": "ST-400M",
                "rated_power_w": 400
            }
        }
    }
    
    print("Sending inference request...")
    print(f"  Module: {payload['module_id']}")
    print(f"  Image size: 640x512")
    print(f"  Max temp: {payload['metadata']['thermal']['max_temperature']:.1f}°C")
    print()
    
    # Send request
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("✓ Inference successful!")
        print()
        print("Results:")
        print(f"  Defect Type:    {result['defect_type']}")
        print(f"  Severity:       {result['severity']} ({result['severity_score']:.2f})")
        print(f"  Confidence:     {result['confidence']:.2%}")
        print(f"  Temperature Δ:  {result['temperature_delta']:.1f}°C")
        print(f"  Max Temp:       {result['max_temperature']:.1f}°C")
        print(f"  Affected Cells: {result['affected_cells']}")
        print(f"  Processing:     {result['processing_time_ms']:.1f}ms")
        print()
        print("Recommendations:")
        for rec in result['recommendations']:
            print(f"  [{rec['priority']}] {rec['action']}: {rec['description']}")
        print()
        return True
    else:
        print(f"✗ Request failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return False


if __name__ == '__main__':
    print("="*60)
    print("Testing ML Inference with Demo Thermal Image")
    print("="*60)
    print()
    
    success = test_inference()
    
    if success:
        print("="*60)
        print("Test Complete!")
        print("="*60)
    else:
        print("Test failed. Check the ML service logs.")
