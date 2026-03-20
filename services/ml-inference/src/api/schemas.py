"""API schemas for ML inference service."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class DefectResult(BaseModel):
    """Single defect detection result."""
    defect_type: str
    confidence: float
    severity: str
    severity_score: float
    temperature_delta: float
    affected_cells: List[int]
    recommendations: List[Dict[str, str]]


class InferenceResult(BaseModel):
    """Complete inference result for a module."""
    module_id: str
    inspection_id: str
    image_id: str
    defect_type: str
    severity: str
    severity_score: float
    confidence: float
    temperature_delta: float
    max_temperature: float
    ambient_temperature: float
    affected_cells: List[int]
    recommendations: List[Dict[str, str]]
    processing_time_ms: float
    timestamp: str
    model_version: str


class InferenceRequest(BaseModel):
    """Request for single inference."""
    module_id: str
    inspection_id: str
    image_id: str
    thermal_data: str = Field(..., description="Base64 encoded thermal image")
    metadata: Dict = Field(default_factory=dict)


class BatchInferenceRequest(BaseModel):
    """Request for batch inference."""
    requests: List[InferenceRequest]
    max_batch_size: int = Field(default=8, ge=1, le=32)


class BatchInferenceResponse(BaseModel):
    """Response for batch inference."""
    results: List[InferenceResult]
    count: int
    total_processing_time_ms: float
    avg_time_per_image_ms: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    device: str
    models_loaded: bool
    stages: int


class StageInfo(BaseModel):
    """Information about a pipeline stage."""
    stage: int
    name: str
    model: str
    input_shape: str
    output: str
    latency_ms: float
    description: str


class PipelineInfoResponse(BaseModel):
    """Pipeline information response."""
    stages: List[StageInfo]
    total_latency_ms: float
    device: str


class DefectTypeResponse(BaseModel):
    """Defect type information."""
    name: str
    description: str
    iec_code: Optional[str] = None


class SeverityLevelResponse(BaseModel):
    """Severity level information."""
    name: str
    description: str
    action: str
