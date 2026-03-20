"""
ML Service Unit Tests
=====================

Tests for ML inference pipeline, feature extraction, and preprocessing.

Run: pytest tests/ -v
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.features.extractor import (
    extract_temperature_stats,
    extract_spatial_gradients,
    extract_glcm_texture,
    extract_morphological_features,
    extract_fft_features,
    extract_stage3_features,
    extract_stage4_features,
    normalize_features,
    FeatureResult
)
from src.features.thermal import (
    normalize_temperature,
    compute_temperature_statistics,
    temperature_to_pseudo_rgb,
    ThermalMetadata,
    ThermalImage,
)


# ==================== Fixtures ====================

@pytest.fixture
def sample_thermal_crop() -> np.ndarray:
    """Generate sample thermal crop for testing."""
    # Create realistic thermal pattern with hotspot
    crop = np.random.normal(50, 5, (128, 128)).astype(np.float32)
    
    # Add hotspot
    crop[40:60, 50:70] += 25
    
    return crop


@pytest.fixture
def sample_full_image() -> np.ndarray:
    """Generate sample full thermal image."""
    # Create realistic thermal pattern
    image = np.random.normal(45, 8, (640, 512)).astype(np.float32)
    
    # Add module pattern
    for i in range(0, 640, 80):
        for j in range(0, 512, 64):
            image[i:i+78, j:j+62] += 10
    
    return image


@pytest.fixture
def sample_metadata() -> dict:
    """Sample metadata for testing."""
    return {
        'neighbor_temps': [45.0, 46.0, 44.5, 45.5],
        'string_mean': 48.5,
        'array_mean': 47.2,
        'ambient_temp': 35.0,
        'expected_temp': 52.0,
        'string_position': 5,
        'row_index': 2,
        'col_index': 3,
        'time_of_day': 14,
        'irradiance': 850,
        'wind_speed': 3.5,
        'humidity': 45
    }


# ==================== Stage 3 Feature Tests ====================

class TestTemperatureStats:
    """Tests for temperature statistics extraction."""
    
    def test_extract_temperature_stats_shape(self, sample_thermal_crop):
        """Test output shape."""
        features, names = extract_temperature_stats(sample_thermal_crop)
        assert features.shape == (11,)
        assert len(names) == 11
    
    def test_extract_temperature_stats_values(self, sample_thermal_crop):
        """Test feature values are reasonable."""
        features, _ = extract_temperature_stats(sample_thermal_crop)
        
        # mean should be around 50 (base) + some from hotspot
        assert 45 < features[0] < 60  # mean
        # max should be around 75 (50 + 25 hotspot)
        assert 70 < features[1] < 80  # max
        # min should be around 35-45
        assert 30 < features[2] < 50  # min
    
    def test_feature_names(self, sample_thermal_crop):
        """Test feature names are correct."""
        _, names = extract_temperature_stats(sample_thermal_crop)
        expected_names = [
            'mean_temp', 'max_temp', 'min_temp', 'std_temp', 'skewness',
            'kurtosis', 'p5_temp', 'p25_temp', 'p50_temp', 'p75_temp', 'p95_temp'
        ]
        assert names == expected_names


class TestSpatialGradients:
    """Tests for spatial gradient extraction."""
    
    def test_extract_spatial_gradients_shape(self, sample_thermal_crop):
        """Test output shape."""
        features, names = extract_spatial_gradients(sample_thermal_crop)
        assert features.shape == (16,)
        assert len(names) == 16
    
    def test_gradient_magnitude(self, sample_thermal_crop):
        """Test gradient magnitude is positive."""
        features, _ = extract_spatial_gradients(sample_thermal_crop)
        
        # All gradient features should be non-negative
        assert np.all(features[:8] >= 0)
        
        # Direction histogram should sum to ~1
        hist_sum = np.sum(features[8:16])
        assert 0.9 < hist_sum < 1.1


class TestGLCMTexture:
    """Tests for GLCM texture extraction."""
    
    def test_extract_glcm_texture_shape(self, sample_thermal_crop):
        """Test output shape."""
        features, names = extract_glcm_texture(sample_thermal_crop)
        assert features.shape == (16,)
        assert len(names) == 16
    
    def test_contrast_values(self, sample_thermal_crop):
        """Test contrast values are reasonable."""
        features, _ = extract_glcm_texture(sample_thermal_crop)
        
        # Contrast should be positive
        assert np.all(features[0:4] >= 0)
        
        # Energy should be between 0 and 1
        assert np.all((features[8:12] >= 0) & (features[8:12] <= 1))


class TestMorphologicalFeatures:
    """Tests for morphological feature extraction."""
    
    def test_extract_morphological_shape(self, sample_thermal_crop):
        """Test output shape."""
        features, names = extract_morphological_features(sample_thermal_crop)
        assert features.shape == (8,)
        assert len(names) == 8
    
    def test_hot_region_count(self, sample_thermal_crop):
        """Test hot region detection."""
        features, _ = extract_morphological_features(sample_thermal_crop)
        
        # Should detect at least 1 hot region (the hotspot we added)
        assert features[0] >= 1


class TestFFTFeatures:
    """Tests for FFT spectral feature extraction."""
    
    def test_extract_fft_features_shape(self, sample_thermal_crop):
        """Test output shape."""
        features, names = extract_fft_features(sample_thermal_crop)
        assert features.shape == (12,)
        assert len(names) == 12
    
    def test_energy_values(self, sample_thermal_crop):
        """Test energy values are positive."""
        features, _ = extract_fft_features(sample_thermal_crop)
        
        # Energy values should be positive
        assert np.all(features[1:4] >= 0)
        
        # Energy ratios should be between 0 and 1
        assert np.all((features[4:6] >= 0) & (features[4:6] <= 1))


class TestStage3Features:
    """Tests for complete Stage 3 feature extraction."""
    
    def test_extract_stage3_features_shape(self, sample_thermal_crop, sample_metadata):
        """Test output shape."""
        result = extract_stage3_features(sample_thermal_crop, sample_metadata)
        assert result.features.shape == (77,)
        assert len(result.feature_names) == 77
    
    def test_feature_groups(self, sample_thermal_crop, sample_metadata):
        """Test feature groups are correct."""
        result = extract_stage3_features(sample_thermal_crop, sample_metadata)
        
        # Check feature groups
        assert result.feature_names[0:11] == [
            'mean_temp', 'max_temp', 'min_temp', 'std_temp', 'skewness',
            'kurtosis', 'p5_temp', 'p25_temp', 'p50_temp', 'p75_temp', 'p95_temp'
        ]
        
        # Last 8 should be context features
        assert result.feature_names[-8:] == [
            'string_position', 'row_index', 'col_index', 'time_of_day',
            'irradiance', 'ambient_temp', 'wind_speed', 'humidity'
        ]


# ==================== Stage 4 Feature Tests ====================

class TestStage4Features:
    """Tests for Stage 4 anomaly detection features."""
    
    def test_extract_stage4_features_shape(self, sample_thermal_crop):
        """Test output shape."""
        result = extract_stage4_features(sample_thermal_crop)
        assert result.features.shape == (96,)
        assert len(result.feature_names) == 96
    
    def test_histogram_normalization(self, sample_thermal_crop):
        """Test histogram is normalized."""
        result = extract_stage4_features(sample_thermal_crop)
        
        # First 64 features are histogram
        histogram = result.features[:64]
        
        # Should sum to 1
        assert 0.99 < np.sum(histogram) < 1.01


# ==================== Thermal Utils Tests ====================

class TestNormalizeTemperature:
    """Tests for temperature normalization."""
    
    def test_minmax_normalization(self, sample_thermal_crop):
        """Test min-max normalization."""
        normalized = normalize_temperature(sample_thermal_crop, method='minmax')
        
        # Should be in [0, 1] range
        assert np.all(normalized >= 0)
        assert np.all(normalized <= 1)
        
        # Min should be 0, max should be 1
        assert np.isclose(np.min(normalized), 0, atol=1e-6)
        assert np.isclose(np.max(normalized), 1, atol=1e-6)
    
    def test_zscore_normalization(self, sample_thermal_crop):
        """Test z-score normalization."""
        normalized = normalize_temperature(sample_thermal_crop, method='zscore')
        
        # Should have mean ~0, std ~1
        assert np.isclose(np.mean(normalized), 0, atol=1e-6)
        assert np.isclose(np.std(normalized), 1, atol=0.1)
    
    def test_fixed_normalization(self, sample_thermal_crop):
        """Test fixed range normalization."""
        normalized = normalize_temperature(
            sample_thermal_crop,
            method='fixed',
            range_min=20,
            range_max=80
        )
        
        # Should be in reasonable range
        assert np.all(normalized >= -0.1)
        assert np.all(normalized <= 1.1)


class TestTemperatureStatistics:
    """Tests for temperature statistics computation."""
    
    def test_compute_statistics_keys(self, sample_thermal_crop):
        """Test statistics dictionary keys."""
        stats = compute_temperature_statistics(sample_thermal_crop)
        
        expected_keys = [
            'min', 'max', 'mean', 'median', 'std', 'variance',
            'skewness', 'kurtosis', 'p5', 'p25', 'p75', 'p95', 'p99',
            'iqr', 'range'
        ]
        
        for key in expected_keys:
            assert key in stats
    
    def test_statistics_values(self, sample_thermal_crop):
        """Test statistics values are reasonable."""
        stats = compute_temperature_statistics(sample_thermal_crop)
        
        # Min should be around 35-45
        assert 30 < stats['min'] < 50
        
        # Max should be around 70-80 (with hotspot)
        assert 70 < stats['max'] < 85
        
        # Mean should be around 50
        assert 45 < stats['mean'] < 60


class TestTemperatureToPseudoRGB:
    """Tests for temperature visualization."""
    
    def test_pseudo_rgb_shape(self, sample_thermal_crop):
        """Test output shape."""
        rgb = temperature_to_pseudo_rgb(sample_thermal_crop, colormap='ironbow')
        assert rgb.shape == (*sample_thermal_crop.shape, 3)
        assert rgb.dtype == np.uint8
    
    def test_pseudo_rgb_values(self, sample_thermal_crop):
        """Test RGB values are in valid range."""
        rgb = temperature_to_pseudo_rgb(sample_thermal_crop, colormap='ironbow')
        
        # Values should be 0-255
        assert np.all(rgb >= 0)
        assert np.all(rgb <= 255)
    
    def test_colormaps(self, sample_thermal_crop):
        """Test different colormaps."""
        colormaps = ['ironbow', 'grayscale', 'rainbow', 'thermal']
        
        for colormap in colormaps:
            rgb = temperature_to_pseudo_rgb(sample_thermal_crop, colormap=colormap)
            assert rgb.shape == (*sample_thermal_crop.shape, 3)


# ==================== Integration Tests ====================

class TestPipelineIntegration:
    """Integration tests for complete pipeline."""
    
    def test_feature_extraction_pipeline(self, sample_thermal_crop, sample_metadata):
        """Test complete feature extraction."""
        # Stage 3 features
        stage3_result = extract_stage3_features(sample_thermal_crop, sample_metadata)
        assert stage3_result.features.shape == (77,)
        
        # Stage 4 features
        stage4_result = extract_stage4_features(sample_thermal_crop)
        assert stage4_result.features.shape == (96,)
    
    def test_normalize_features(self):
        """Test feature normalization."""
        features = np.random.randn(10, 77) * 10 + 50
        
        scaler_params = {
            'mean': np.mean(features, axis=0),
            'std': np.std(features, axis=0)
        }
        
        normalized = normalize_features(features, scaler_params)
        
        # Normalized features should have mean ~0, std ~1
        assert np.allclose(np.mean(normalized, axis=0), 0, atol=0.1)
        assert np.allclose(np.std(normalized, axis=0), 1, atol=0.2)


# ==================== Edge Cases ====================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_crop(self):
        """Test with constant temperature crop."""
        crop = np.ones((128, 128)) * 50
        
        features, names = extract_temperature_stats(crop)
        
        # std should be 0
        assert features[3] == 0
        
        # All percentiles should be same
        assert features[6] == features[10]
    
    def test_nan_handling(self):
        """Test handling of NaN values."""
        crop = np.random.normal(50, 5, (128, 128))
        crop[50:60, 50:60] = np.nan
        
        # Should not raise
        stats = compute_temperature_statistics(crop)
        
        # Statistics should be computed from valid values only
        assert np.isfinite(stats['mean'])
    
    def test_very_small_crop(self):
        """Test with very small crop."""
        crop = np.random.normal(50, 5, (16, 16))
        
        # Should work with small crops
        features, names = extract_temperature_stats(crop)
        assert features.shape == (11,)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
