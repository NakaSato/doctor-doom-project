"""
ML Inference Service - Port 8001
================================

Four-stage cascade pipeline for thermal solar panel defect detection.

Performance: <35ms per module (edge), <15ms (cloud with GPU)
Supports both ONNX (cloud) and CoreML (Mac M2 edge) models.
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Callable, Awaitable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    PROMETHEUS_INSTRUMENTATOR_AVAILABLE = True
except ImportError:
    PROMETHEUS_INSTRUMENTATOR_AVAILABLE = False
    Instrumentator = None

from .api import router, set_pipeline
from .api.schemas import HealthResponse
from .pipeline import MLPipeline
from .utils import (
    get_settings,
    setup_logging,
    get_logger,
    MLServiceError,
    PipelineNotInitializedError,
    RequestValidationMiddleware,
    metrics,
)

# Initialize settings and logging
settings = get_settings()
logger = setup_logging(level=settings.log_level)


# Global pipeline instance
pipeline: Optional[MLPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting ML Inference Service...")
    start_time = time.time()
    
    # Initialize pipeline
    global pipeline
    pipeline = MLPipeline(model_path=str(settings.model_path))
    
    # Load models
    logger.info(f"Loading models from {settings.model_path}...")
    await asyncio.get_event_loop().run_in_executor(None, pipeline.load_models)
    
    # Set pipeline in API router
    set_pipeline(pipeline)
    
    # Record metrics
    startup_time = time.time() - start_time
    logger.info(f"Service started in {startup_time:.2f}s")
    metrics.update_active_models(4)  # 4 stages
    
    for stage in range(1, 5):
        metrics.set_model_loaded(stage, True)
    
    logger.info(f"Service started on {settings.host}:{settings.port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ML Inference Service...")
    if pipeline:
        pipeline.unload_models()
    logger.info("Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="ML Inference Service",
    description="Four-stage cascade pipeline for thermal solar panel defect detection",
    version="1.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(RequestValidationMiddleware)

# Add Prometheus metrics
if settings.enable_metrics and PROMETHEUS_INSTRUMENTATOR_AVAILABLE:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
elif settings.enable_metrics and not PROMETHEUS_INSTRUMENTATOR_AVAILABLE:
    logger.warning("Prometheus metrics enabled but prometheus_fastapi_instrumentator not installed")


# ==================== Exception Handlers ====================

@app.exception_handler(MLServiceError)
async def ml_service_error_handler(request: Request, exc: MLServiceError):
    """Handle ML service exceptions."""
    logger.error(
        f"ML Service Error: {exc.code} - {exc.message}",
        extra={"status_code": exc.status_code, **exc.details}
    )
    metrics.record_error(exc.code)
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Request validation error: {exc.errors()}")
    metrics.record_error("VALIDATION_ERROR")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions."""
    logger.exception(f"Unhandled exception: {str(exc)}")
    metrics.record_error("INTERNAL_ERROR")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "details": {"type": type(exc).__name__},
            }
        },
    )


# ==================== Request Logging Middleware ====================

@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]) -> Response:
    """Log all requests with timing."""
    start_time = time.time()
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_s": process_time,
        }
    )
    
    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Include API router
app.include_router(router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Service health check."""
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version="1.0.0",
        device=settings.device,
        models_loaded=pipeline is not None and pipeline.models_loaded,
        stages=4,
    )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "service": "ml-inference",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        workers=settings.workers,
    )
