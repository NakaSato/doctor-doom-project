"""API module for ML inference service."""

from .routes import router, set_pipeline
from .schemas import (
    InferenceRequest,
    InferenceResult,
    BatchInferenceRequest,
    BatchInferenceResponse,
    HealthResponse,
    PipelineInfoResponse,
    StageInfo,
    DefectTypeResponse,
    SeverityLevelResponse,
)

__all__ = [
    "router",
    "set_pipeline",
    # Schemas
    "InferenceRequest",
    "InferenceResult",
    "BatchInferenceRequest",
    "BatchInferenceResponse",
    "HealthResponse",
    "PipelineInfoResponse",
    "StageInfo",
    "DefectTypeResponse",
    "SeverityLevelResponse",
]
