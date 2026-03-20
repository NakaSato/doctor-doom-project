"""
Custom Exception Hierarchy for ML Inference Service
====================================================

Provides structured error handling with proper error codes and HTTP status mappings.
"""
from typing import Any, Dict, Optional


class MLServiceError(Exception):
    """Base exception for ML Inference Service."""
    
    def __init__(
        self,
        message: str,
        code: str = "ML_SERVICE_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "status_code": self.status_code,
                "details": self.details,
            }
        }


# ==================== Model Errors (4xx) ====================

class ModelNotFoundError(MLServiceError):
    """Requested model not found."""
    
    def __init__(self, model_name: str, stage: Optional[int] = None):
        message = f"Model not found: {model_name}"
        if stage:
            message += f" (Stage {stage})"
        super().__init__(
            message=message,
            code="MODEL_NOT_FOUND",
            status_code=404,
            details={"model_name": model_name, "stage": stage}
        )


class ModelLoadError(MLServiceError):
    """Failed to load model."""
    
    def __init__(self, model_name: str, reason: str):
        super().__init__(
            message=f"Failed to load model {model_name}: {reason}",
            code="MODEL_LOAD_ERROR",
            status_code=503,
            details={"model_name": model_name, "reason": reason}
        )


class ModelNotInitializedError(MLServiceError):
    """Model not initialized."""
    
    def __init__(self, stage: int):
        super().__init__(
            message=f"Model for stage {stage} not initialized",
            code="MODEL_NOT_INITIALIZED",
            status_code=503,
            details={"stage": stage}
        )


# ==================== Inference Errors (4xx/5xx) ====================

class InferenceError(MLServiceError):
    """Base class for inference-related errors."""
    
    def __init__(
        self,
        message: str,
        code: str = "INFERENCE_ERROR",
        status_code: int = 500,
        module_id: Optional[str] = None,
        inspection_id: Optional[str] = None
    ):
        details = {}
        if module_id:
            details["module_id"] = module_id
        if inspection_id:
            details["inspection_id"] = inspection_id
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            details=details
        )


class InferenceTimeoutError(InferenceError):
    """Inference timed out."""
    
    def __init__(
        self,
        timeout_ms: int,
        module_id: Optional[str] = None,
        inspection_id: Optional[str] = None
    ):
        super().__init__(
            message=f"Inference timed out after {timeout_ms}ms",
            code="INFERENCE_TIMEOUT",
            status_code=504,
            module_id=module_id,
            inspection_id=inspection_id
        )


class InvalidInputError(InferenceError):
    """Invalid input data."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        module_id: Optional[str] = None
    ):
        details = {"field": field} if field else {}
        if module_id:
            details["module_id"] = module_id
        super().__init__(
            message=message,
            code="INVALID_INPUT",
            status_code=400,
            module_id=module_id,
        )


class ThermalDataError(InvalidInputError):
    """Invalid or corrupted thermal data."""
    
    def __init__(
        self,
        message: str,
        camera_type: Optional[str] = None,
        module_id: Optional[str] = None
    ):
        details = {"camera_type": camera_type} if camera_type else {}
        if module_id:
            details["module_id"] = module_id
        super().__init__(
            message=f"Thermal data error: {message}",
            code="THERMAL_DATA_ERROR",
            field="thermal_data",
            module_id=module_id,
        )


class ThermalParserError(ThermalDataError):
    """Failed to parse thermal image."""
    
    def __init__(
        self,
        camera_type: Optional[str] = None,
        detail: Optional[str] = None,
        module_id: Optional[str] = None
    ):
        message = "Failed to parse thermal image"
        if camera_type:
            message += f" ({camera_type})"
        if detail:
            message += f": {detail}"
        super().__init__(
            message=message,
            camera_type=camera_type,
            module_id=module_id,
        )


# ==================== Pipeline Errors (5xx) ====================

class PipelineError(InferenceError):
    """Base class for pipeline errors."""
    pass


class PipelineStageError(PipelineError):
    """Error in specific pipeline stage."""
    
    def __init__(
        self,
        stage: int,
        message: str,
        module_id: Optional[str] = None,
        inspection_id: Optional[str] = None
    ):
        super().__init__(
            message=f"Stage {stage} failed: {message}",
            code=f"PIPELINE_STAGE_{stage}_ERROR",
            status_code=500,
            module_id=module_id,
            inspection_id=inspection_id,
        )
        self.stage = stage


class PipelineNotInitializedError(PipelineError):
    """Pipeline not initialized."""
    
    def __init__(self):
        super().__init__(
            message="ML Pipeline not initialized. Check service startup logs.",
            code="PIPELINE_NOT_INITIALIZED",
            status_code=503,
        )


# ==================== Configuration Errors (5xx) ====================

class ConfigurationError(MLServiceError):
    """Configuration error."""
    
    def __init__(self, message: str, setting: Optional[str] = None):
        details = {"setting": setting} if setting else {}
        super().__init__(
            message=f"Configuration error: {message}",
            code="CONFIGURATION_ERROR",
            status_code=500,
            details=details
        )


class RedisConnectionError(MLServiceError):
    """Failed to connect to Redis."""
    
    def __init__(self, host: str, port: int, reason: str):
        super().__init__(
            message=f"Failed to connect to Redis at {host}:{port}: {reason}",
            code="REDIS_CONNECTION_ERROR",
            status_code=503,
            details={"host": host, "port": port, "reason": reason}
        )


# ==================== Exception Handler for FastAPI ====================

def create_error_response(exception: MLServiceError) -> Dict[str, Any]:
    """Create standardized error response."""
    return exception.to_dict()


# Exception to HTTP status code mapping
EXCEPTION_STATUS_MAP = {
    ModelNotFoundError: 404,
    ModelLoadError: 503,
    ModelNotInitializedError: 503,
    InvalidInputError: 400,
    ThermalDataError: 400,
    ThermalParserError: 400,
    InferenceTimeoutError: 504,
    PipelineNotInitializedError: 503,
    ConfigurationError: 500,
    RedisConnectionError: 503,
}
