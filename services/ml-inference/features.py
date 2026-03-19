"""
ML Feature Extractors
=====================

Feature extraction modules for Stage 3 (Severity Scoring) and Stage 4 (Anomaly Detection).

Stage 3: 77-dimensional feature vector
- Temperature statistics (11)
- Spatial gradients (16)
- Delta-T relative (6)
- GLCM texture (16)
- Morphological (8)
- FFT spectral (12)
- Context (8)

Stage 4: 96-dimensional feature vector
- Temperature histogram (64)
- Spatial gradient vector (32)
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy import ndimage, stats
from skimage.feature import graycomatrix, graycoprops
from skimage.measure import label, regionprops
from skimage import morphology
import cv2


@dataclass
class FeatureResult:
    """Result of feature extraction."""
    features: np.ndarray
    feature_names: List[str]
    metadata: Dict


# ==================== Stage 3: Severity Scoring Features (77-dim) ====================

def extract_temperature_stats(thermal_crop: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    """
    Extract 11 temperature statistics from thermal crop.
    
    Features:
    - mean, max, min, std
    - skewness, kurtosis
    - percentiles: p5, p25, p50, p75, p95
    """
    temps = thermal_crop.flatten()
    
    features = np.array([
        np.mean(temps),           # 0: mean_temp
        np.max(temps),            # 1: max_temp
        np.min(temps),            # 2: min_temp
        np.std(temps),            # 3: std_temp
        stats.skew(temps),        # 4: skewness
        stats.kurtosis(temps),    # 5: kurtosis
        np.percentile(temps, 5),   # 6: p5_temp
        np.percentile(temps, 25),  # 7: p25_temp
        np.percentile(temps, 50),  # 8: p50_temp
        np.percentile(temps, 75),  # 9: p75_temp
        np.percentile(temps, 95)   # 10: p95_temp
    ])
    
    names = [
        'mean_temp', 'max_temp', 'min_temp', 'std_temp', 'skewness',
        'kurtosis', 'p5_temp', 'p25_temp', 'p50_temp', 'p75_temp', 'p95_temp'
    ]
    
    return features, names


def extract_spatial_gradients(thermal_crop: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    """
    Extract 16 spatial gradient features using Sobel filters.
    
    Features:
    - Sobel H/V mean, std
    - Gradient magnitude mean, std, max, p95
    - Direction histogram (8 bins)
    """
    # Sobel filters
    sobel_x = ndimage.sobel(thermal_crop, axis=1)  # Horizontal
    sobel_y = ndimage.sobel(thermal_crop, axis=0)  # Vertical
    magnitude = np.hypot(sobel_x, sobel_y)
    direction = np.arctan2(sobel_y, sobel_x)
    
    # Basic statistics
    features = [
        np.mean(sobel_x), np.std(sobel_x),   # 0-1: sobel_h_mean, sobel_h_std
        np.mean(sobel_y), np.std(sobel_y),   # 2-3: sobel_v_mean, sobel_v_std
        np.mean(magnitude), np.std(magnitude),  # 4-5: sobel_mag_mean, sobel_mag_std
        np.max(magnitude),                      # 6: sobel_mag_max
        np.percentile(magnitude, 95)            # 7: sobel_mag_p95
    ]
    
    # Direction histogram (8 bins)
    hist, _ = np.histogram(direction.flatten(), bins=8, range=(-np.pi, np.pi))
    hist_normalized = hist.astype(np.float32) / hist.sum()
    features.extend(hist_normalized.tolist())  # 8-15: direction_hist_0-7
    
    features_array = np.array(features)
    
    names = [
        'sobel_h_mean', 'sobel_h_std', 'sobel_v_mean', 'sobel_v_std',
        'sobel_mag_mean', 'sobel_mag_std', 'sobel_mag_max', 'sobel_mag_p95',
        'direction_hist_0', 'direction_hist_1', 'direction_hist_2', 'direction_hist_3',
        'direction_hist_4', 'direction_hist_5', 'direction_hist_6', 'direction_hist_7'
    ]
    
    return features_array, names


def extract_delta_t_relative(
    thermal_crop: np.ndarray,
    neighbor_temps: List[float],
    string_mean: float,
    array_mean: float,
    ambient_temp: float,
    expected_temp: float
) -> Tuple[np.ndarray, List[str]]:
    """
    Extract 6 delta-T features relative to various references.
    """
    max_temp = np.max(thermal_crop)
    
    features = np.array([
        max_temp - np.mean(neighbor_temps),  # 0: delta_t_neighbors
        max_temp - string_mean,               # 1: delta_t_string
        max_temp - array_mean,                # 2: delta_t_array
        max_temp - ambient_temp,              # 3: delta_t_ambient
        max_temp - expected_temp,             # 4: delta_t_expected
        (max_temp - ambient_temp) / 50.0      # 5: delta_t_normalized
    ])
    
    names = [
        'delta_t_neighbors', 'delta_t_string', 'delta_t_array',
        'delta_t_ambient', 'delta_t_expected', 'delta_t_normalized'
    ]
    
    return features, names


def extract_glcm_texture(thermal_crop: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    """
    Extract 16 GLCM texture features at 4 angles.
    
    Features per angle (0°, 45°, 90°, 135°):
    - Contrast, Correlation, Energy, Homogeneity
    """
    # Normalize to [0, 1] first
    normalized = (thermal_crop - thermal_crop.min()) / (thermal_crop.max() - thermal_crop.min() + 1e-8)
    
    # Quantize to 64 levels (0-63)
    image = (normalized * 63).astype(np.uint8)
    
    # Ensure max value is 63
    image = np.clip(image, 0, 63)

    # Compute GLCM at 4 angles
    glcm = graycomatrix(
        image,
        distances=[1],
        angles=[0, np.pi/4, np.pi/2, 3*np.pi/4],
        levels=64,
        symmetric=True,
        normed=True
    )
    
    # Extract 4 properties × 4 angles = 16 features
    contrast = graycoprops(glcm, 'contrast').flatten()       # 0-3
    correlation = graycoprops(glcm, 'correlation').flatten() # 4-7
    energy = graycoprops(glcm, 'energy').flatten()           # 8-11
    homogeneity = graycoprops(glcm, 'homogeneity').flatten() # 12-15
    
    features = np.concatenate([contrast, correlation, energy, homogeneity])
    
    names = []
    props = ['contrast', 'correlation', 'energy', 'homogeneity']
    angles = ['0', '45', '90', '135']
    for prop in props:
        for angle in angles:
            names.append(f'glcm_{prop}_{angle}')
    
    return features, names


def extract_morphological_features(thermal_crop: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    """
    Extract 8 morphological features from hot regions.
    """
    # Threshold for hot regions (mean + 2*std)
    threshold = np.mean(thermal_crop) + 2 * np.std(thermal_crop)
    binary = thermal_crop > threshold
    
    # Morphological closing
    closed = morphology.closing(binary, morphology.disk(3))
    
    # Connected components
    labeled = label(closed)
    regions = regionprops(labeled)
    
    if len(regions) == 0:
        features = np.zeros(8)
    else:
        areas = [r.area for r in regions]
        eccentricities = [r.eccentricity for r in regions]
        solidities = [r.solidity for r in regions]
        perimeters = [r.perimeter for r in regions]
        
        # Compute dispersion
        centroids = np.array([r.centroid for r in regions])
        center = np.mean(centroids, axis=0)
        dispersion = np.mean(np.linalg.norm(centroids - center, axis=1))
        
        features = np.array([
            len(regions),                     # 0: hot_region_count
            np.sum(areas) / thermal_crop.size,# 1: hot_area_ratio
            np.max(areas),                    # 2: hot_area_max
            np.mean(areas),                   # 3: hot_area_mean
            np.mean(eccentricities),          # 4: hot_eccentricity_mean
            np.mean(solidities),              # 5: hot_solidity_mean
            np.mean(perimeters),              # 6: hot_perimeter_mean
            dispersion                        # 7: hot_dispersion
        ])
    
    names = [
        'hot_region_count', 'hot_area_ratio', 'hot_area_max', 'hot_area_mean',
        'hot_eccentricity_mean', 'hot_solidity_mean', 'hot_perimeter_mean', 'hot_dispersion'
    ]
    
    return features, names


def extract_fft_features(thermal_crop: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    """
    Extract 12 FFT spectral features for periodic pattern detection.
    """
    from scipy import fftpack
    
    # 2D FFT
    f_transform = fftpack.fft2(thermal_crop)
    f_shift = fftpack.fftshift(f_transform)
    magnitude = np.abs(f_shift)
    
    h, w = magnitude.shape
    cy, cx = h // 2, w // 2

    # Distance from center
    r = np.sqrt((np.arange(h) - cy)[:, None]**2 + (np.arange(w) - cx)[None, :]**2)
    r_norm = r / np.max(r)
    
    # Frequency bands
    low_mask = r_norm < 0.1
    mid_mask = (r_norm >= 0.1) & (r_norm < 0.5)
    high_mask = r_norm >= 0.5
    
    total_energy = np.sum(magnitude**2)
    low_energy = np.sum(magnitude[low_mask]**2)
    mid_energy = np.sum(magnitude[mid_mask]**2)
    high_energy = np.sum(magnitude[high_mask]**2)
    
    # Spectral centroid and spread
    spectral_centroid = np.sum(r_norm * magnitude**2) / total_energy
    spectral_spread = np.sqrt(
        np.sum((r_norm - spectral_centroid)**2 * magnitude**2) / total_energy
    )
    
    # Orientation analysis
    # Create 2D angle grid
    y_coords, x_coords = np.meshgrid(np.arange(h) - cy, np.arange(w) - cx, indexing='ij')
    angles = np.arctan2(y_coords, x_coords)
    orientation_hist, _ = np.histogram(
        angles.flatten(),
        bins=18,
        weights=magnitude.flatten(),
        range=(-np.pi, np.pi)
    )
    dominant_orientation = np.argmax(orientation_hist) * 10
    orientation_strength = np.max(orientation_hist) / np.sum(orientation_hist)
    
    # Periodicity
    periodicity = np.max(magnitude[cy-10:cy+10, cx-10:cx+10]) / np.mean(magnitude)
    
    # Spectral entropy
    prob = magnitude**2 / total_energy
    entropy = -np.sum(prob * np.log2(prob + 1e-10))
    
    features = np.array([
        magnitude[cy, cx],              # 0: fft_dc_component
        low_energy,                     # 1: fft_low_freq_energy
        mid_energy,                     # 2: fft_mid_freq_energy
        high_energy,                    # 3: fft_high_freq_energy
        low_energy / total_energy,      # 4: fft_energy_ratio_low
        high_energy / total_energy,     # 5: fft_energy_ratio_high
        spectral_centroid,              # 6: fft_spectral_centroid
        spectral_spread,                # 7: fft_spectral_spread
        dominant_orientation,           # 8: fft_orientation_dominant
        orientation_strength,           # 9: fft_orientation_strength
        periodicity,                    # 10: fft_periodicity
        entropy                         # 11: fft_entropy
    ])
    
    names = [
        'fft_dc_component', 'fft_low_freq_energy', 'fft_mid_freq_energy',
        'fft_high_freq_energy', 'fft_energy_ratio_low', 'fft_energy_ratio_high',
        'fft_spectral_centroid', 'fft_spectral_spread', 'fft_orientation_dominant',
        'fft_orientation_strength', 'fft_periodicity', 'fft_entropy'
    ]
    
    return features, names


def extract_context_features(context: Dict) -> Tuple[np.ndarray, List[str]]:
    """
    Extract 8 context features (environmental and positional).
    """
    # Normalize features
    features = np.array([
        context.get('string_position', 0) / 20.0,    # 0: string_position
        context.get('row_index', 0) / 50.0,          # 1: row_index
        context.get('col_index', 0) / 30.0,          # 2: col_index
        context.get('time_of_day', 12) / 24.0,       # 3: time_of_day
        context.get('irradiance', 800) / 1200.0,     # 4: irradiance
        context.get('ambient_temp', 25) / 50.0,      # 5: ambient_temp
        context.get('wind_speed', 5) / 20.0,         # 6: wind_speed
        context.get('humidity', 50) / 100.0          # 7: humidity
    ])
    
    names = [
        'string_position', 'row_index', 'col_index', 'time_of_day',
        'irradiance', 'ambient_temp', 'wind_speed', 'humidity'
    ]
    
    return features, names


def extract_stage3_features(
    thermal_crop: np.ndarray,
    metadata: Dict
) -> FeatureResult:
    """
    Extract complete 77-dimensional feature vector for Stage 3 severity scoring.
    
    Args:
        thermal_crop: Module thermal image [128, 128]
        metadata: Dictionary containing:
            - neighbor_temps, string_mean, array_mean, ambient_temp, expected_temp
            - string_position, row_index, col_index, time_of_day
            - irradiance, wind_speed, humidity
    
    Returns:
        FeatureResult with 77-dim feature vector
    """
    all_features = []
    all_names = []
    
    # 1. Temperature stats (11)
    feats, names = extract_temperature_stats(thermal_crop)
    all_features.append(feats)
    all_names.extend(names)
    
    # 2. Spatial gradients (16)
    feats, names = extract_spatial_gradients(thermal_crop)
    all_features.append(feats)
    all_names.extend(names)
    
    # 3. Delta-T relative (6)
    feats, names = extract_delta_t_relative(
        thermal_crop,
        neighbor_temps=metadata.get('neighbor_temps', [np.mean(thermal_crop)] * 4),
        string_mean=metadata.get('string_mean', np.mean(thermal_crop)),
        array_mean=metadata.get('array_mean', np.mean(thermal_crop)),
        ambient_temp=metadata.get('ambient_temp', 25.0),
        expected_temp=metadata.get('expected_temp', np.mean(thermal_crop) + 10)
    )
    all_features.append(feats)
    all_names.extend(names)
    
    # 4. GLCM texture (16)
    feats, names = extract_glcm_texture(thermal_crop)
    all_features.append(feats)
    all_names.extend(names)
    
    # 5. Morphological (8)
    feats, names = extract_morphological_features(thermal_crop)
    all_features.append(feats)
    all_names.extend(names)
    
    # 6. FFT spectral (12)
    feats, names = extract_fft_features(thermal_crop)
    all_features.append(feats)
    all_names.extend(names)
    
    # 7. Context (8)
    feats, names = extract_context_features(metadata)
    all_features.append(feats)
    all_names.extend(names)
    
    # Concatenate all features
    feature_vector = np.concatenate(all_features)
    
    return FeatureResult(
        features=feature_vector,
        feature_names=all_names,
        metadata={'total_features': len(feature_vector)}
    )


# ==================== Stage 4: Anomaly Detection Features (96-dim) ====================

def extract_temperature_histogram(
    thermal_crop: np.ndarray,
    n_bins: int = 64
) -> Tuple[np.ndarray, List[str]]:
    """
    Extract 64-bin normalized temperature histogram.
    """
    temps = thermal_crop.flatten()
    
    hist, _ = np.histogram(
        temps,
        bins=n_bins,
        range=(temps.min(), temps.max()),
        density=False
    )
    
    # Normalize to sum = 1
    hist_normalized = hist.astype(np.float32) / len(temps)
    
    names = [f'temp_hist_bin_{i}' for i in range(n_bins)]
    
    return hist_normalized, names


def extract_gradient_features(thermal_crop: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    """
    Extract 32 spatial gradient features (multi-scale Sobel).
    """
    features = []
    scales = [3, 5, 7]
    
    for scale in scales:
        # Sobel filters
        sobel_h = cv2.Sobel(thermal_crop, cv2.CV_64F, 1, 0, ksize=scale)
        sobel_v = cv2.Sobel(thermal_crop, cv2.CV_64F, 0, 1, ksize=scale)
        sobel_d1 = ndimage.sobel(thermal_crop, axis=0)
        sobel_d2 = ndimage.sobel(thermal_crop, axis=1)
        
        # Extract statistics per direction
        for grad in [sobel_h, sobel_v, sobel_d1, sobel_d2]:
            features.extend([
                np.mean(np.abs(grad)),
                np.std(np.abs(grad)),
                np.max(np.abs(grad)),
                np.percentile(np.abs(grad), 95)
            ])
    
    # Total: 3 scales × 4 directions × 4 stats = 48 features
    # Reduce to 32 via simple averaging
    features_array = np.array(features)
    
    # Simple reduction: average adjacent features
    reduced = np.zeros(32)
    for i in range(32):
        if i < len(features_array):
            reduced[i] = features_array[i]
        else:
            reduced[i] = np.mean(features_array[max(0, i-16):min(len(features_array), i+16)])
    
    names = [f'gradient_feat_{i}' for i in range(32)]
    
    return reduced, names


def extract_stage4_features(thermal_crop: np.ndarray) -> FeatureResult:
    """
    Extract complete 96-dimensional feature vector for Stage 4 anomaly detection.
    
    Args:
        thermal_crop: Module thermal image [128, 128]
    
    Returns:
        FeatureResult with 96-dim feature vector
    """
    all_features = []
    all_names = []
    
    # 1. Temperature histogram (64)
    feats, names = extract_temperature_histogram(thermal_crop, n_bins=64)
    all_features.append(feats)
    all_names.extend(names)
    
    # 2. Spatial gradient vector (32)
    feats, names = extract_gradient_features(thermal_crop)
    all_features.append(feats)
    all_names.extend(names)
    
    # Concatenate all features
    feature_vector = np.concatenate(all_features)
    
    return FeatureResult(
        features=feature_vector,
        feature_names=all_names,
        metadata={'total_features': len(feature_vector)}
    )


# ==================== Utility Functions ====================

def normalize_features(features: np.ndarray, scaler_params: Dict) -> np.ndarray:
    """
    Normalize features using pre-computed scaler parameters.
    
    Args:
        features: Raw feature vector
        scaler_params: Dictionary with 'mean' and 'std' arrays
    
    Returns:
        Normalized feature vector
    """
    mean = scaler_params.get('mean', np.zeros_like(features))
    std = scaler_params.get('std', np.ones_like(features))
    
    return (features - mean) / (std + 1e-8)


def get_feature_importance(model, feature_names: List[str], top_k: int = 10) -> List[Dict]:
    """
    Extract top-K feature importances from trained model.
    
    Args:
        model: Trained model (XGBoost, etc.)
        feature_names: List of feature names
        top_k: Number of top features to return
    
    Returns:
        List of {feature, importance} dictionaries
    """
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    else:
        # Default to uniform
        importances = np.ones(len(feature_names)) / len(feature_names)
    
    # Sort by importance
    indices = np.argsort(importances)[::-1][:top_k]
    
    return [
        {'feature': feature_names[i], 'importance': float(importances[i])}
        for i in indices
    ]
