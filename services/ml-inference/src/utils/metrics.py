"""
Prometheus Metrics for ML Inference Service
============================================

Custom metrics for monitoring ML pipeline performance and health.
"""
import time
from typing import Dict, Optional, Any
from collections import defaultdict

try:
    from prometheus_client import Counter, Histogram, Gauge, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def inc(self, *args, **kwargs): pass
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def observe(self, *args, **kwargs): pass
        def time(self): return _DummyTimer()
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def observe(self, *args, **kwargs): pass
        def time(self): return _DummyTimer()
    
    class _DummyTimer:
        def __enter__(self): pass
        def __exit__(self, *args): pass


class _DummyTimer:
    def __enter__(self): pass
    def __exit__(self, *args): pass


# ==================== Metrics Definitions ====================

# Inference counters
INFERENCE_REQUESTS_TOTAL = Counter(
    "ml_inference_requests_total",
    "Total number of inference requests",
    ["status", "defect_type", "severity"],
)

INFERENCE_ERRORS_TOTAL = Counter(
    "ml_inference_errors_total",
    "Total number of inference errors",
    ["error_type", "stage"],
)

# Latency metrics
INFERENCE_LATENCY_SECONDS = Histogram(
    "ml_inference_latency_seconds",
    "Inference latency in seconds",
    ["stage"],
    buckets=[
        0.001, 0.0025, 0.005, 0.0075, 0.01, 0.025, 0.05, 0.075, 0.1,
        0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0,
    ],
)

PIPELINE_LATENCY_SECONDS = Histogram(
    "ml_pipeline_latency_seconds",
    "Complete pipeline latency in seconds",
    ["device"],
    buckets=[
        0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 0.15, 0.2,
        0.3, 0.5, 0.75, 1.0,
    ],
)

STAGE_LATENCY_SECONDS = Summary(
    "ml_stage_latency_seconds",
    "Individual stage latency in seconds",
    ["stage", "model"],
)

# Model metrics
MODEL_INFO = Gauge(
    "ml_model_info",
    "Model version and metadata",
    ["stage", "version", "format", "device"],
)

MODEL_LOADED = Gauge(
    "ml_model_loaded",
    "Whether model is loaded (1) or not (0)",
    ["stage"],
)

ACTIVE_MODELS = Gauge(
    "ml_active_models",
    "Number of active models in memory"
)

# Resource metrics
BATCH_SIZE = Histogram(
    "ml_batch_size",
    "Batch size for inference",
    buckets=[1, 2, 4, 8, 16, 32],
)

MEMORY_USAGE_BYTES = Gauge(
    "ml_memory_usage_bytes",
    "Memory usage in bytes",
    ["type"],  # model_cache, inference, total
)

# Quality metrics
DEFECT_DETECTION_RATE = Counter(
    "ml_defect_detection_total",
    "Total defects detected by type and severity",
    ["defect_type", "severity", "confidence_bucket"],
)

CONFIDENCE_SCORE = Histogram(
    "ml_confidence_score",
    "Model confidence scores",
    ["stage"],
    buckets=[0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.925, 0.95, 0.975, 0.99, 1.0],
)


# ==================== Metrics Manager ====================

class MetricsManager:
    """Manage Prometheus metrics for ML service."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and PROMETHEUS_AVAILABLE
        self._stage_timers: Dict[int, float] = {}
    
    # Request tracking
    def record_request(
        self,
        status: str = "success",
        defect_type: str = "unknown",
        severity: str = "unknown"
    ):
        """Record an inference request."""
        if self.enabled:
            INFERENCE_REQUESTS_TOTAL.labels(
                status=status,
                defect_type=defect_type,
                severity=severity
            ).inc()
    
    def record_error(self, error_type: str, stage: Optional[int] = None):
        """Record an inference error."""
        if self.enabled:
            INFERENCE_ERRORS_TOTAL.labels(
                error_type=error_type,
                stage=stage or "unknown"
            ).inc()
    
    # Latency tracking
    def record_latency(self, latency_seconds: float, stage: str = "total"):
        """Record inference latency."""
        if self.enabled:
            INFERENCE_LATENCY_SECONDS.labels(stage=stage).observe(latency_seconds)
    
    def record_pipeline_latency(self, latency_seconds: float, device: str = "edge"):
        """Record complete pipeline latency."""
        if self.enabled:
            PIPELINE_LATENCY_SECONDS.labels(device=device).observe(latency_seconds)
    
    def stage_timer(self, stage: int, model: str):
        """Context manager for timing a stage."""
        if self.enabled:
            return STAGE_LATENCY_SECONDS.labels(stage=stage, model=model).time()
        return _DummyTimer()
    
    # Model tracking
    def set_model_info(
        self,
        stage: int,
        version: str,
        model_format: str,
        device: str
    ):
        """Set model information."""
        if self.enabled:
            MODEL_INFO.labels(
                stage=stage,
                version=version,
                format=model_format,
                device=device
            ).set(1)
    
    def set_model_loaded(self, stage: int, loaded: bool = True):
        """Set model loaded status."""
        if self.enabled:
            MODEL_LOADED.labels(stage=stage).set(1 if loaded else 0)
    
    def update_active_models(self, count: int):
        """Update active models count."""
        if self.enabled:
            ACTIVE_MODELS.set(count)
    
    # Batch and resource tracking
    def record_batch_size(self, size: int):
        """Record batch size."""
        if self.enabled:
            BATCH_SIZE.observe(size)
    
    def record_memory_usage(self, usage_bytes: int, type: str = "total"):
        """Record memory usage."""
        if self.enabled:
            MEMORY_USAGE_BYTES.labels(type=type).set(usage_bytes)
    
    # Quality tracking
    def record_defect_detection(
        self,
        defect_type: str,
        severity: str,
        confidence: float
    ):
        """Record a defect detection."""
        if self.enabled:
            # Determine confidence bucket
            if confidence >= 0.99:
                bucket = "0.99-1.0"
            elif confidence >= 0.95:
                bucket = "0.95-0.99"
            elif confidence >= 0.90:
                bucket = "0.90-0.95"
            elif confidence >= 0.80:
                bucket = "0.80-0.90"
            else:
                bucket = "<0.80"
            
            DEFECT_DETECTION_RATE.labels(
                defect_type=defect_type,
                severity=severity,
                confidence_bucket=bucket
            ).inc()
            
            CONFIDENCE_SCORE.labels(stage="final").observe(confidence)
    
    def record_confidence(self, confidence: float, stage: int):
        """Record confidence score for a stage."""
        if self.enabled:
            CONFIDENCE_SCORE.labels(stage=stage).observe(confidence)


# Global metrics manager instance
metrics = MetricsManager()


def get_metrics_manager() -> MetricsManager:
    """Get the global metrics manager."""
    return metrics
