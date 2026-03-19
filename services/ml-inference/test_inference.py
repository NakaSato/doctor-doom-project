#!/usr/bin/env python3
"""Test ML inference endpoint."""
import requests
import base64
import numpy as np
import json

# Generate sample thermal data
thermal_data = np.random.randn(640, 512).astype(np.float32) * 10 + 50
thermal_b64 = base64.b64encode(thermal_data.tobytes()).decode()

# Send inference request
response = requests.post(
    'http://localhost:8001/api/v1/ml/infer',
    json={
        'module_id': 'mod_001_05',
        'inspection_id': 'insp_001',
        'image_id': 'img_demo_001',
        'thermal_data': thermal_b64,
        'metadata': {
            'ambient_temp': 35.0,
            'irradiance': 850
        }
    }
)

if response.status_code == 200:
    result = response.json()
    print("=" * 70)
    print("ML Inference Result")
    print("=" * 70)
    print()
    print(f"Module ID:      {result['module_id']}")
    print(f"Defect Type:    {result['defect_type']}")
    print(f"Severity:       {result['severity']} ({result['severity_score']:.3f})")
    print(f"Confidence:     {result['confidence']:.1%}")
    print(f"Temperature Δ:  {result['temperature_delta']:.1f}°C")
    print(f"Max Temp:       {result['max_temperature']:.1f}°C")
    print(f"Ambient Temp:   {result['ambient_temperature']:.1f}°C")
    print(f"Affected Cells: {result['affected_cells']}")
    print(f"Anomaly Score:  {result['anomaly_score']:.3f}")
    print(f"Processing:     {result['processing_time_ms']:.1f}ms")
    print()
    
    if result['recommendations']:
        print("Recommendations:")
        for rec in result['recommendations']:
            print(f"  [{rec['priority']}] {rec['action']}")
            print(f"      {rec['description']}")
    
    print()
    print("=" * 70)
    print("✓ Inference successful!")
    print("=" * 70)
else:
    print(f"✗ Request failed: {response.status_code}")
    print(response.text)
