"""
Thermal Image Preprocessing Utilities
======================================

Utilities for loading, processing, and augmenting thermal imagery
from DJI Mavic 3T and other radiometric cameras.

Supports:
- RJPEG (Radiometric JPEG) parsing using thermal_parser
- Temperature calibration
- Normalization and standardization
- Module crop extraction
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import cv2
import json
import logging

logger = logging.getLogger(__name__)

# Import thermal_parser for R-JPEG parsing
try:
    from thermal_parser import Thermal
    THERMAL_PARSER_AVAILABLE = True
    THERMAL_PARSER_ERROR = None
except ImportError as e:
    THERMAL_PARSER_AVAILABLE = False
    THERMAL_PARSER_ERROR = f"Import error: {e}"
except NotImplementedError as e:
    THERMAL_PARSER_AVAILABLE = False
    THERMAL_PARSER_ERROR = f"Platform not supported: {e}"
except Exception as e:
    THERMAL_PARSER_AVAILABLE = False
    THERMAL_PARSER_ERROR = f"Error: {e}"


@dataclass
class ThermalMetadata:
    """Metadata from radiometric thermal image."""
    # Temperature calibration
    emissivity: float = 0.95
    object_distance_m: float = 50.0
    atmospheric_temp_c: float = 20.0
    reflected_temp_c: float = 20.0
    relative_humidity: float = 50.0
    
    # Camera settings
    gain: str = 'low'
    shutter: str = 'auto'
    
    # Environmental
    ambient_temp_c: float = 25.0
    irradiance_w_m2: float = 800.0
    
    # GPS/Position
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude_m: Optional[float] = None
    
    # Timestamp
    capture_time: Optional[str] = None


@dataclass
class ThermalImage:
    """Processed thermal image with metadata."""
    # Temperature data (°C)
    temperature: np.ndarray  # 2D array of temperatures
    
    # Metadata
    metadata: ThermalMetadata
    
    # Visible light overlay (optional)
    visible: Optional[np.ndarray] = None
    
    # Image info (computed from temperature)
    width: int = 0
    height: int = 0
    min_temp: float = 0.0
    max_temp: float = 0.0
    mean_temp: float = 0.0


def load_rjpeg(file_path: Union[str, Path]) -> ThermalImage:
    """
    Load radiometric JPEG (RJPEG) from DJI Mavic 3T using thermal_parser.
    
    Args:
        file_path: Path to RJPEG file
    
    Returns:
        ThermalImage with temperature data
    
    Supported cameras:
    - DJI Mavic 3T (M3T)
    - DJI H20T / H20N
    - DJI M30T / M3TD
    - DJI H30T
    - FLIR series (AX8, B60, E40, T640)
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Use thermal_parser if available
    if THERMAL_PARSER_AVAILABLE:
        try:
            thermal_parser = Thermal(dtype=np.float32)
            temperature = thermal_parser.parse(filepath_image=str(file_path))
            
            if isinstance(temperature, np.ndarray):
                # Load metadata from Exif if available
                metadata = _load_exif_metadata(file_path)
                
                return ThermalImage(
                    temperature=temperature,
                    metadata=metadata,
                    width=temperature.shape[1],
                    height=temperature.shape[0],
                    min_temp=float(np.nanmin(temperature)),
                    max_temp=float(np.nanmax(temperature)),
                    mean_temp=float(np.nanmean(temperature))
                )
        except Exception as e:
            logger.warning(f"thermal_parser failed: {e}, using fallback")
    else:
        if THERMAL_PARSER_ERROR:
            logger.debug(f"thermal_parser not available: {THERMAL_PARSER_ERROR}")
    
    # Fallback to basic loading
    return _load_thermal_fallback(file_path)


def _load_exif_metadata(file_path: Path) -> ThermalMetadata:
    """Load metadata from Exif data."""
    metadata = ThermalMetadata()
    
    try:
        import piexif
        exif_data = piexif.load(str(file_path))
        
        # Parse DJI thermal metadata from Exif
        if 'maker_note' in exif_data:
            # DJI-specific metadata parsing
            # This would need custom implementation based on DJI format
            pass
        
        # Parse standard Exif tags
        if '0th' in exif_data:
            # GPS data
            if piexif.GPSIFD.GPSLatitude in exif_data['0th']:
                # Parse GPS coordinates
                pass
        
        if 'Exif' in exif_data:
            # Timestamp
            if piexif.ExifIFD.DateTimeOriginal in exif_data['Exif']:
                metadata.capture_time = exif_data['Exif'][piexif.ExifIFD.DateTimeOriginal]
                
    except Exception as e:
        logger.debug(f"Could not parse Exif: {e}")
    
    return metadata


def _load_thermal_fallback(file_path: Path) -> ThermalImage:
    """
    Fallback thermal loading when radiometric data unavailable.
    Creates estimated temperature from visible image.
    """
    # Load as grayscale
    image = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
    
    if image is None:
        raise ValueError(f"Could not load image: {file_path}")
    
    # Estimate temperature (not accurate, for demo only)
    temp_min, temp_max = 20, 80  # Typical operating range
    temperature = (image.astype(np.float32) / 255.0) * (temp_max - temp_min) + temp_min
    
    return ThermalImage(
        temperature=temperature,
        visible=None,
        metadata=ThermalMetadata(),
        width=temperature.shape[1],
        height=temperature.shape[0],
        min_temp=float(np.nanmin(temperature)),
        max_temp=float(np.nanmax(temperature)),
        mean_temp=float(np.nanmean(temperature))
    )


def normalize_temperature(
    temperature: np.ndarray,
    method: str = 'minmax',
    range_min: Optional[float] = None,
    range_max: Optional[float] = None
) -> np.ndarray:
    """
    Normalize temperature data to [0, 1] range.
    
    Args:
        temperature: Temperature array (°C)
        method: Normalization method ('minmax', 'zscore', 'fixed')
        range_min: Fixed minimum for 'fixed' method
        range_max: Fixed maximum for 'fixed' method
    
    Returns:
        Normalized temperature array
    """
    if method == 'minmax':
        temp_min = np.nanmin(temperature)
        temp_max = np.nanmax(temperature)
        return (temperature - temp_min) / (temp_max - temp_min + 1e-8)
    
    elif method == 'zscore':
        mean = np.nanmean(temperature)
        std = np.nanstd(temperature)
        return (temperature - mean) / (std + 1e-8)
    
    elif method == 'fixed':
        if range_min is None or range_max is None:
            raise ValueError("range_min and range_max required for fixed normalization")
        return (temperature - range_min) / (range_max - range_min + 1e-8)
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def extract_module_crop(
    thermal_image: ThermalImage,
    bbox: Tuple[int, int, int, int],
    target_size: Tuple[int, int] = (128, 128)
) -> np.ndarray:
    """
    Extract and resize module crop from thermal image.
    
    Args:
        thermal_image: Source thermal image
        bbox: Bounding box (x_min, y_min, x_max, y_max)
        target_size: Target crop size (width, height)
    
    Returns:
        Cropped and resized temperature array
    """
    x_min, y_min, x_max, y_max = bbox
    
    # Extract crop
    crop = thermal_image.temperature[y_min:y_max, x_min:x_max]
    
    # Resize to target size
    resized = cv2.resize(
        crop,
        target_size,
        interpolation=cv2.INTER_LINEAR
    )
    
    return resized


def apply_thermal_augmentation(
    temperature: np.ndarray,
    augmentations: List[str],
    **kwargs
) -> np.ndarray:
    """
    Apply thermal-specific augmentations.
    
    Args:
        temperature: Temperature array
        augmentations: List of augmentation names
        **kwargs: Augmentation parameters
    
    Returns:
        Augmented temperature array
    """
    result = temperature.copy()
    
    for aug in augmentations:
        if aug == 'noise':
            # Add thermal noise
            sigma = kwargs.get('noise_sigma', 0.02)
            noise = np.random.normal(0, sigma, result.shape)
            result = result + noise
        
        elif aug == 'temp_shift':
            # Shift temperature
            shift = kwargs.get('temp_shift_range', 5.0)
            delta = np.random.uniform(-shift, shift)
            result = result + delta
        
        elif aug == 'contrast':
            # Adjust thermal contrast
            factor = kwargs.get('contrast_factor', 1.0)
            mean = np.mean(result)
            result = mean + (result - mean) * factor
        
        elif aug == 'occlusion':
            # Simulate occlusion (cutout)
            n_holes = kwargs.get('n_holes', 5)
            size = kwargs.get('hole_size', 16)
            h, w = result.shape
            
            for _ in range(n_holes):
                x = np.random.randint(0, w - size)
                y = np.random.randint(0, h - size)
                result[y:y+size, x:x+size] = np.mean(result)
    
    return result


def temperature_to_pseudo_rgb(
    temperature: np.ndarray,
    colormap: str = 'ironbow',
    normalize: bool = True
) -> np.ndarray:
    """
    Convert temperature array to pseudo-RGB visualization.
    
    Args:
        temperature: Temperature array (°C)
        colormap: Colormap name ('ironbow', 'grayscale', 'rainbow', 'thermal')
        normalize: Whether to normalize before applying colormap
    
    Returns:
        RGB image (H, W, 3)
    """
    if normalize:
        # Normalize to [0, 1]
        temp_min = np.nanmin(temperature)
        temp_max = np.nanmax(temperature)
        normalized = (temperature - temp_min) / (temp_max - temp_min + 1e-8)
    else:
        normalized = temperature
    
    # Clip to valid range
    normalized = np.clip(normalized, 0, 1)
    
    # Apply colormap
    if colormap == 'ironbow':
        # Ironbow-like colormap (blue → red → yellow → white)
        rgb = np.zeros((*normalized.shape, 3), dtype=np.uint8)
        
        # Blue channel (high temps)
        rgb[:, :, 0] = (normalized * 255).astype(np.uint8)
        
        # Green channel (mid temps)
        rgb[:, :, 1] = ((normalized > 0.33) * (normalized - 0.33) * 3 * 255).astype(np.uint8)
        
        # Red channel (low temps)
        rgb[:, :, 2] = ((normalized > 0.66) * (normalized - 0.66) * 3 * 255).astype(np.uint8)
        
    elif colormap == 'grayscale':
        gray = (normalized * 255).astype(np.uint8)
        rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    
    elif colormap == 'rainbow':
        # Use OpenCV's rainbow colormap
        gray = (normalized * 255).astype(np.uint8)
        rgb = cv2.applyColorMap(gray, cv2.COLORMAP_RAINBOW)
        rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
    
    elif colormap == 'thermal':
        # Thermal-like (black → red → yellow → white)
        gray = (normalized * 255).astype(np.uint8)
        rgb = cv2.applyColorMap(gray, cv2.COLORMAP_HOT)
        rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
    
    else:
        raise ValueError(f"Unknown colormap: {colormap}")
    
    return rgb


def compute_temperature_statistics(temperature: np.ndarray) -> Dict[str, float]:
    """
    Compute comprehensive temperature statistics.
    
    Args:
        temperature: Temperature array (°C)
    
    Returns:
        Dictionary of statistics
    """
    from scipy import stats
    
    temps = temperature.flatten()
    valid_temps = temps[~np.isnan(temps)]
    
    return {
        'min': float(np.min(valid_temps)),
        'max': float(np.max(valid_temps)),
        'mean': float(np.mean(valid_temps)),
        'median': float(np.median(valid_temps)),
        'std': float(np.std(valid_temps)),
        'variance': float(np.var(valid_temps)),
        'skewness': float(stats.skew(valid_temps)),
        'kurtosis': float(stats.kurtosis(valid_temps)),
        'p5': float(np.percentile(valid_temps, 5)),
        'p25': float(np.percentile(valid_temps, 25)),
        'p75': float(np.percentile(valid_temps, 75)),
        'p95': float(np.percentile(valid_temps, 95)),
        'p99': float(np.percentile(valid_temps, 99)),
        'iqr': float(np.percentile(valid_temps, 75) - np.percentile(valid_temps, 25)),
        'range': float(np.max(valid_temps) - np.min(valid_temps))
    }


# Example usage
if __name__ == '__main__':
    # Load thermal image
    thermal = load_rjpeg('sample_thermal.rjpeg')
    
    print(f"Image size: {thermal.width}x{thermal.height}")
    print(f"Temperature range: {thermal.min_temp:.1f}°C - {thermal.max_temp:.1f}°C")
    print(f"Mean temperature: {thermal.mean_temp:.1f}°C")
    
    # Normalize
    normalized = normalize_temperature(thermal.temperature, method='minmax')
    
    # Extract module crop
    bbox = (100, 100, 228, 228)  # Example bounding box
    crop = extract_module_crop(thermal, bbox, target_size=(128, 128))
    
    # Apply augmentation
    augmented = apply_thermal_augmentation(
        crop,
        augmentations=['noise', 'temp_shift'],
        noise_sigma=0.02,
        temp_shift_range=3.0
    )
    
    # Convert to RGB for visualization
    rgb = temperature_to_pseudo_rgb(augmented, colormap='ironbow')
    
    # Compute statistics
    stats = compute_temperature_statistics(crop)
    print(f"\nCrop statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value:.2f}")
