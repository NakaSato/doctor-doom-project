"""Feature extraction for Stage 3 and Stage 4."""

from .extractor import (
    extract_temperature_stats,
    extract_spatial_gradients,
    extract_delta_t_features,
    extract_glcm_texture,
    extract_morphological_features,
    extract_fft_spectral,
    extract_context_features,
    extract_stage3_features,
    extract_stage4_features,
    FeatureResult,
)

from .thermal import (
    preprocess_thermal_image,
    parse_thermal_metadata,
    normalize_thermal,
    crop_module,
)

__all__ = [
    # Extractor
    "extract_temperature_stats",
    "extract_spatial_gradients",
    "extract_delta_t_features",
    "extract_glcm_texture",
    "extract_morphological_features",
    "extract_fft_spectral",
    "extract_context_features",
    "extract_stage3_features",
    "extract_stage4_features",
    "FeatureResult",
    # Thermal
    "preprocess_thermal_image",
    "parse_thermal_metadata",
    "normalize_thermal",
    "crop_module",
]
