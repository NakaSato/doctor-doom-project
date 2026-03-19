#!/usr/bin/env python3
"""
Test thermal_parser with sample DJI thermal image.

Usage:
    uv run python test_thermal_parser.py [image_path]
    
If no image path provided, creates a test with mock data.
"""
import sys
import numpy as np
from pathlib import Path

from thermal_parser import Thermal


def test_thermal_parser(image_path: str = None):
    """Test thermal_parser with provided image or mock data."""
    
    print("=" * 60)
    print("thermal_parser Test")
    print("=" * 60)
    print()
    
    # Initialize thermal parser
    thermal = Thermal(dtype=np.float32)
    print(f"✓ Thermal parser initialized")
    print(f"  Class: {Thermal}")
    print(f"  dtype: np.float32")
    print()
    
    if image_path and Path(image_path).exists():
        # Parse real image
        print(f"Parsing: {image_path}")
        print("-" * 60)
        
        temperature = thermal.parse(filepath_image=image_path)
        
        print(f"✓ Successfully parsed thermal image")
        print(f"  Type: {type(temperature)}")
        print(f"  Shape: {temperature.shape}")
        print(f"  dtype: {temperature.dtype}")
        print()
        
        # Statistics
        print(f"Temperature Statistics:")
        print(f"  Min:  {np.nanmin(temperature):.2f}°C")
        print(f"  Max:  {np.nanmax(temperature):.2f}°C")
        print(f"  Mean: {np.nanmean(temperature):.2f}°C")
        print(f"  Std:  {np.nanstd(temperature):.2f}°C")
        print()
        
        # Check for valid temperature range (DJI cameras)
        if np.nanmin(temperature) < -40 or np.nanmax(temperature) > 150:
            print(f"⚠ Warning: Temperature values outside expected range (-40°C to 150°C)")
        else:
            print(f"✓ Temperature values in expected range")
        
    else:
        # Mock test
        print("No image provided. Running mock test...")
        print("-" * 60)
        print()
        
        # Create mock thermal data (simulating 640x512 DJI Mavic 3T)
        mock_temp = np.random.normal(45, 8, (512, 640)).astype(np.float32)
        
        # Add some "hotspots"
        mock_temp[200:250, 300:350] += 25  # Hotspot 1
        mock_temp[100:150, 400:450] += 15  # Hotspot 2
        
        print(f"✓ Created mock thermal image")
        print(f"  Shape: {mock_temp.shape}")
        print(f"  dtype: {mock_temp.dtype}")
        print()
        
        print(f"Temperature Statistics:")
        print(f"  Min:  {np.nanmin(mock_temp):.2f}°C")
        print(f"  Max:  {np.nanmax(mock_temp):.2f}°C")
        print(f"  Mean: {np.nanmean(mock_temp):.2f}°C")
        print(f"  Std:  {np.nanstd(mock_temp):.2f}°C")
        print()
        
        # Simulate what thermal_parser.parse() would return
        print(f"Expected output from thermal_parser.parse():")
        print(f"  - Returns numpy.ndarray")
        print(f"  - Shape: (height, width)")
        print(f"  - Values: Temperature in °C")
        print(f"  - dtype: float32 (as specified)")
    
    print()
    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)
    
    # Supported cameras
    print()
    print("Supported Cameras (thermal_parser):")
    print("-" * 60)
    print("DJI R-JPEG:")
    print("  • Mavic 3T (M3T), M2EA")
    print("  • H20T, H20N, H30T")
    print("  • M30T, M3TD (DJI Dock 2)")
    print()
    print("FLIR R-JPEG:")
    print("  • FLIR AX8, B60, E40, T640")
    print()


if __name__ == '__main__':
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    test_thermal_parser(image_path)
