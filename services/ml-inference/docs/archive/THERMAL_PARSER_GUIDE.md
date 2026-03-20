# thermal_parser Integration Guide

## Overview

The ML Inference Service now includes **thermal_parser** for parsing radiometric JPEG (R-JPEG) images from DJI and FLIR thermal cameras.

## Installation

```bash
# Install with uv (recommended)
uv sync

# thermal-parser will be installed from GitHub:
# https://github.com/SanNianYiSi/thermal_parser.git
```

## Supported Cameras

### DJI R-JPEG (Data3.0)
- **Mavic 3 Series**: M3T, M2EA
- **Zenmuse**: H20T, H20N, H30T, H30N
- **Matrice**: M30T, M30
- **Dock**: M3TD (DJI Dock 2)

### FLIR R-JPEG
- FLIR AX8
- FLIR B60
- FLIR E40
- FLIR T640

## Usage

### Basic Usage

```python
import numpy as np
from thermal_parser import Thermal

# Initialize thermal parser
thermal = Thermal(dtype=np.float32)

# Parse R-JPEG image
temperature = thermal.parse(filepath_image='path/to/DJI_M3T.jpg')

# Result is a numpy array of temperatures in °C
assert isinstance(temperature, np.ndarray)
print(f"Shape: {temperature.shape}")  # (height, width)
print(f"Temperature range: {temperature.min():.1f}°C to {temperature.max():.1f}°C")
```

### With Doctor Doom ML Service

```python
from ml_inference.thermal_utils import load_rjpeg

# Load R-JPEG with automatic metadata
thermal_image = load_rjpeg('path/to/thermal_image.jpg')

# Access temperature data
temperature = thermal_image.temperature  # numpy array
metadata = thermal_image.metadata        # camera settings, GPS, etc.

# Get statistics
print(f"Min: {thermal_image.min_temp:.1f}°C")
print(f"Max: {thermal_image.max_temp:.1f}°C")
print(f"Mean: {thermal_image.mean_temp:.1f}°C")
```

### Advanced Usage

```python
from thermal_parser import Thermal
import numpy as np

# Initialize with specific dtype
thermal_f32 = Thermal(dtype=np.float32)  # 32-bit float (recommended)
thermal_f64 = Thermal(dtype=np.float64)  # 64-bit float (higher precision)

# Parse multiple images
images = ['img1.jpg', 'img2.jpg', 'img3.jpg']
for img_path in images:
    temp = thermal_f32.parse(filepath_image=img_path)
    
    # Process temperature data
    hotspot_mask = temp > 70  # Find areas > 70°C
    num_hotspots = np.sum(hotspot_mask)
    
    print(f"{img_path}: {num_hotspots} hotspots detected")
```

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| **Linux x64** | ✅ Full Support | Recommended for production |
| **Windows x64** | ✅ Full Support | Tested on Windows 10/11 |
| **macOS (Apple Silicon)** | ⚠️ Fallback | Uses fallback loading |
| **macOS (Intel)** | ⚠️ Fallback | Uses fallback loading |

### macOS Fallback

On macOS, thermal_parser may not be available due to platform-specific dependencies. The service automatically falls back to basic loading:

```python
from ml_inference.thermal_utils import load_rjpeg

# On macOS, this uses fallback loading
thermal_image = load_rjpeg('thermal_image.jpg')

# Fallback estimates temperature from visible image
# Not as accurate as radiometric data, but functional for testing
```

For production use on macOS, consider:
1. Running in Docker (Linux container)
2. Using pre-processed temperature data
3. Deploying to Linux server

## Troubleshooting

### "NotImplementedError: currently not supported for running on this platform"

This error occurs on macOS. The service handles this automatically:

```python
# In thermal_utils.py
try:
    from thermal_parser import Thermal
    THERMAL_PARSER_AVAILABLE = True
except NotImplementedError:
    THERMAL_PARSER_AVAILABLE = False  # Uses fallback
```

### "ModuleNotFoundError: No module named 'thermal_parser'"

Ensure dependencies are installed:

```bash
# With uv
uv sync

# Or install directly
pip install git+https://github.com/SanNianYiSi/thermal_parser.git
```

### Invalid Temperature Values

If temperatures seem incorrect:

1. **Check camera type**: Ensure image is from supported camera
2. **Verify R-JPEG format**: Must be radiometric JPEG, not regular JPEG
3. **Check Emissivity**: Default is 0.95, adjust if needed

```python
# Adjust emissivity (if supported by camera)
thermal = Thermal(emissivity=0.90)  # Default: 0.95
```

## Example: Solar Panel Inspection

```python
from thermal_parser import Thermal
import numpy as np
import cv2

# Initialize
thermal = Thermal(dtype=np.float32)

# Parse DJI Mavic 3T thermal image
temp_data = thermal.parse('solar_panel_inspection.jpg')

# Detect hotspots (temperature > ambient + 20°C)
ambient = 35.0  # °C
threshold = ambient + 20.0
hotspots = temp_data > threshold

# Count and locate hotspots
num_hotspots = np.sum(hotspots)
hotspot_coords = np.column_stack(np.where(hotspots))

print(f"Detected {num_hotspots} potential defects")

# Visualize
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.imshow(temp_data, cmap='inferno')
plt.colorbar(label='Temperature (°C)')
plt.title(f'Thermal Image - {num_hotspots} hotspots')

plt.subplot(1, 2, 2)
plt.imshow(hotspots, cmap='gray')
plt.title('Hotspot Detection')

plt.tight_layout()
plt.savefig('analysis.png', dpi=150)
```

## API Reference

### Thermal Class

```python
class Thermal:
    """
    DJI/FLIR R-JPEG thermal image parser.
    
    Args:
        dtype: Output data type (np.float32 or np.float64)
        emissivity: Emissivity value (default: 0.95)
        object_distance_m: Distance to object in meters (default: 50)
        atmospheric_temp_c: Atmospheric temperature (default: 20)
        reflected_temp_c: Reflected temperature (default: 20)
        relative_humidity: Relative humidity % (default: 50)
    """
    
    def parse(self, filepath_image: str) -> np.ndarray:
        """
        Parse R-JPEG image and extract temperature data.
        
        Args:
            filepath_image: Path to R-JPEG file
            
        Returns:
            numpy.ndarray of temperatures in °C
        """
```

## Resources

- [thermal_parser GitHub](https://github.com/SanNianYiSi/thermal_parser)
- [DJI Thermal SDK](https://www.dji.com/cn/downloads/softwares/dji-thermal-sdk)
- [DJI DTAT3](https://www.dji.com/global/downloads/softwares/dji-dtat3)

## License

thermal_parser is licensed under its own terms. See the [original repository](https://github.com/SanNianYiSi/thermal_parser) for details.
