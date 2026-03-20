"""API routes for ML inference service."""

import base64
import time
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, HTTPException

from ..pipeline import MLPipeline, DefectType, SeverityLevel
from ..utils import (
    get_logger,
    metrics,
    ThermalDataValidator,
    ThermalDataError,
    InvalidInputError,
    PipelineNotInitializedError,
    InferenceTimeoutError,
    PipelineStageError,
)
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

logger = get_logger("api")

router = APIRouter(prefix="/api/v1", tags=["inference"])

# Global pipeline instance (set during app startup)
_pipeline: MLPipeline = None


def set_pipeline(ml_pipeline: MLPipeline):
    """Set the global pipeline instance."""
    global _pipeline
    _pipeline = ml_pipeline


def _get_pipeline() -> MLPipeline:
    """Get pipeline or raise error."""
    if _pipeline is None:
        raise PipelineNotInitializedError()
    return _pipeline


@router.post("/infer", response_model=InferenceResult)
async def infer(request: InferenceRequest) -> InferenceResult:
    """
    Run single module inference through the ML pipeline.
    
    Args:
        request: Inference request with thermal image and metadata
        
    Returns:
        Inference result with defect type, severity, and recommendations
        
    Raises:
        InvalidInputError: If request validation fails
        ThermalDataError: If thermal data is invalid
        PipelineNotInitializedError: If pipeline is not ready
        InferenceTimeoutError: If inference times out
    """
    start_time = time.time()
    
    # Validate request
    try:
        ThermalDataValidator.validate_inference_request({
            "module_id": request.module_id,
            "inspection_id": request.inspection_id,
            "image_id": request.image_id,
            "thermal_data": request.thermal_data,
            "metadata": request.metadata,
        })
    except (InvalidInputError, ThermalDataError) as e:
        metrics.record_error(e.code)
        raise
    
    # Get pipeline
    pipeline = _get_pipeline()
    
    try:
        # Run pipeline
        result = await pipeline.run(
            module_id=request.module_id,
            inspection_id=request.inspection_id,
            image_id=request.image_id,
            thermal_data=request.thermal_data,
            metadata=request.metadata,
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics.record_request(
            status="success",
            defect_type=result.defect_type.value,
            severity=result.severity.value,
        )
        metrics.record_pipeline_latency(processing_time / 1000, device="edge")
        metrics.record_defect_detection(
            defect_type=result.defect_type.value,
            severity=result.severity.value,
            confidence=result.confidence,
        )
        
        logger.info(
            f"Inference completed for {request.module_id}: {result.defect_type.value} ({result.severity.value})",
            extra={
                "module_id": request.module_id,
                "defect_type": result.defect_type.value,
                "severity": result.severity.value,
                "processing_time_ms": processing_time,
            }
        )
        
        return InferenceResult(
            module_id=result.module_id,
            inspection_id=result.inspection_id,
            image_id=result.image_id,
            defect_type=result.defect_type.value,
            severity=result.severity.value,
            severity_score=result.severity_score,
            confidence=result.confidence,
            temperature_delta=result.temperature_delta,
            max_temperature=result.max_temperature,
            ambient_temperature=result.ambient_temperature,
            affected_cells=result.affected_cells,
            recommendations=result.recommendations,
            processing_time_ms=processing_time,
            timestamp=datetime.utcnow().isoformat(),
            model_version="1.0.0",
        )
        
    except TimeoutError:
        metrics.record_error("INFERENCE_TIMEOUT")
        raise InferenceTimeoutError(
            timeout_ms=35000,
            module_id=request.module_id,
            inspection_id=request.inspection_id,
        )
    except PipelineStageError:
        raise
    except Exception as e:
        logger.exception(f"Inference failed for {request.module_id}: {str(e)}")
        metrics.record_error("INFERENCE_ERROR")
        raise


@router.post("/infer/batch", response_model=BatchInferenceResponse)
async def infer_batch(request: BatchInferenceRequest) -> BatchInferenceResponse:
    """
    Run batch inference through the ML pipeline.
    
    Args:
        request: Batch inference request
        
    Returns:
        Batch inference results
    """
    start_time = time.time()
    
    # Get pipeline
    pipeline = _get_pipeline()
    
    results = []
    failed_count = 0
    
    for req in request.requests[: request.max_batch_size]:
        try:
            result = await infer(req)
            results.append(result)
        except Exception as e:
            logger.warning(f"Batch item {req.module_id} failed: {str(e)}")
            failed_count += 1
    
    total_time = (time.time() - start_time) * 1000
    
    # Record batch metrics
    metrics.record_batch_size(len(request.requests))
    metrics.record_request(
        status="partial_success" if failed_count > 0 else "success",
        defect_type="batch",
        severity="n/a",
    )
    
    logger.info(
        f"Batch inference completed: {len(results)}/{len(request.requests)} successful",
        extra={
            "total": len(request.requests),
            "successful": len(results),
            "failed": failed_count,
            "total_time_ms": total_time,
        }
    )
    
    return BatchInferenceResponse(
        results=results,
        count=len(results),
        total_processing_time_ms=total_time,
        avg_time_per_image_ms=total_time / len(results) if results else 0,
    )


@router.get("/stages", response_model=PipelineInfoResponse)
async def get_stages() -> PipelineInfoResponse:
    """Get information about pipeline stages."""
    stages = [
        StageInfo(
            stage=1,
            name="Module Segmentation",
            model="YOLOv8n-seg",
            input_shape="640×512",
            output="Module masks",
            latency_ms=8.0,
            description="Detect and segment solar module from thermal image",
        ),
        StageInfo(
            stage=2,
            name="Defect Detection",
            model="YOLOv8m",
            input_shape="128×128",
            output="12 defect classes",
            latency_ms=12.0,
            description="Classify defect type in module cells",
        ),
        StageInfo(
            stage=3,
            name="Severity Scoring",
            model="XGBoost",
            input_shape="77-dim features",
            output="3-class severity",
            latency_ms=0.3,
            description="Score defect severity using extracted features",
        ),
        StageInfo(
            stage=4,
            name="Anomaly Detection",
            model="ConvAE + IF",
            input_shape="96-dim features",
            output="Anomaly score",
            latency_ms=1.8,
            description="Detect anomalous patterns using autoencoder",
        ),
    ]
    
    return PipelineInfoResponse(
        stages=stages,
        total_latency_ms=sum(s.latency_ms for s in stages),
        device="edge",
    )


@router.get("/defect-types", response_model=List[DefectTypeResponse])
async def get_defect_types() -> List[DefectTypeResponse]:
    """Get supported defect types."""
    return [
        DefectTypeResponse(
            name="hotspot",
            description="Localized heating due to cell mismatch or damage",
            iec_code="IEC 62446-3:B.1",
        ),
        DefectTypeResponse(
            name="cell_anomaly",
            description="Abnormal cell appearance or performance",
            iec_code="IEC 62446-3:B.2",
        ),
        DefectTypeResponse(
            name="delamination",
            description="Separation of module layers",
            iec_code="IEC 62446-3:B.3",
        ),
        DefectTypeResponse(
            name="diode_failure",
            description="Bypass diode malfunction",
            iec_code="IEC 62446-3:B.4",
        ),
        DefectTypeResponse(
            name="crack",
            description="Physical fracture in cell or module",
            iec_code="IEC 62446-3:B.5",
        ),
        DefectTypeResponse(
            name="soiling",
            description="Surface contamination reducing performance",
            iec_code="IEC 62446-3:B.6",
        ),
        DefectTypeResponse(
            name="discoloration",
            description="Abnormal color change indicating degradation",
            iec_code="IEC 62446-3:B.7",
        ),
        DefectTypeResponse(
            name="normal",
            description="No defects detected",
            iec_code=None,
        ),
    ]


@router.get("/severity-levels", response_model=List[SeverityLevelResponse])
async def get_severity_levels() -> List[SeverityLevelResponse]:
    """Get severity level definitions."""
    return [
        SeverityLevelResponse(
            name="low",
            description="Minor defect, minimal impact on performance",
            action="MONITOR",
        ),
        SeverityLevelResponse(
            name="medium",
            description="Moderate defect, reduced performance",
            action="SCHEDULE_INSPECTION",
        ),
        SeverityLevelResponse(
            name="high",
            description="Significant defect, notable performance loss",
            action="PRIORITY_REPLACEMENT",
        ),
        SeverityLevelResponse(
            name="critical",
            description="Severe defect, immediate action required",
            action="IMMEDIATE_REPLACEMENT",
        ),
    ]
