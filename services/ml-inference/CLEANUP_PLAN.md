# ML Inference Service - Cleanup & Modernization Plan

**Date:** 2026-03-20  
**Status:** Planning  
**Priority:** High  

---

## Executive Summary

The ML Inference Service is functionally complete but requires cleanup and modernization for production deployment. This document outlines a comprehensive plan to streamline the codebase, improve maintainability, and prepare for scale.

### Current State

| Aspect | Status | Notes |
|--------|--------|-------|
| **Core Pipeline** | ✅ Complete | 4-stage cascade working |
| **API Service** | ✅ Complete | FastAPI with all endpoints |
| **Documentation** | ⚠️ Excessive | 20+ markdown files, many redundant |
| **Code Organization** | ⚠️ Scattered | Logic spread across many files |
| **Testing** | ⚠️ Minimal | Basic tests exist, low coverage |
| **Docker** | ✅ Complete | Multi-stage build ready |
| **Demo Artifacts** | ⚠️ Clutter | Demo files mixed with production code |
| **Training Scripts** | ⚠️ Unverified | Scripts exist but untested |
| **Notebooks** | ⚠️ Legacy | 2 Jupyter notebooks (may be obsolete) |

---

## 1. File Cleanup Plan

### 1.1 Files to Archive/Delete

#### Documentation Consolidation
**Keep (Essential):**
- `README.md` - Main service documentation
- `ML_ARCHITECTURE.md` - Complete architecture reference
- `TRAINING_GUIDE.md` - Training procedures
- `DATA_FLOW.md` - Data pipeline documentation

**Archive to `docs/archive/`:**
- `ML_IMPLEMENTATION.md` → Merge into ML_ARCHITECTURE.md
- `ML_LIFECYCLE.md` → Merge into TRAINING_GUIDE.md
- `IMPLEMENTATION_SUMMARY.md` → Redundant with FINAL_SUMMARY.md
- `INTEGRATION_GUIDE.md` → Merge into README.md
- `DEMO.md` → Keep only if actively used
- `FINAL_SUMMARY.md` → Archive (snapshot in time)
- `PROJECT_README.md` → Redundant with README.md
- `UV_SETUP.md` → Merge into README.md
- `THERMAL_PARSER_GUIDE.md` → Create single thermal.md guide
- `ML_TRAINING_SETUP_COMPLETE.md` → Archive (time-sensitive)
- `TRAINING_SETUP.md`, `TRAINING_SUMMARY.md`, `TRAINING_COMPLETE.md` → Consolidate
- `TRAINING.md` → Keep as primary training doc
- `WHATS_NEXT.md` → Archive (outdated)
- `MOVE_TO_COLAB.md` → Archive (Colab-specific)
- `MONITOR_TRAINING.sh` → Archive or move to scripts/
- `RUN_TRAINING.sh` → Move to scripts/
- Stage-specific docs (stage1-4).md → Merge into ML_ARCHITECTURE.md
- `YOLOv8m_ARCHITECTURE.md` → Merge into ML_ARCHITECTURE.md

**Delete:**
- `Doctor_Doom_ML_Training_Colab.ipynb` → Obsolete
- `Doctor_Doom_ML_Training.ipynb` → Obsolete (use scripts/)

#### Demo/Temporary Files
**Move to `demo/` directory:**
- `demo_pipeline.py`
- `demo_server.py`
- `create_demo_models.py`
- `setup_demo_models.py`
- `test_demo_inference.py`
- `demo_output/` → Entire directory
- `quick_start.py` → Move to demo/

**Delete after verification:**
- `test_thermal_parser.py` → Integration test exists
- `test_with_real_images.py` → Use proper test suite
- `test_inference.py` → Redundant with tests/

#### Build/Environment
**Consolidate:**
- `requirements.txt` → Keep for backward compatibility
- `pyproject.toml` → Primary dependency source (uv)
- `uv.lock` → Keep (locked versions)

### 1.2 Proposed New Structure

```
services/ml-inference/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app (moved from root)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py              # API endpoints
│   │   ├── dependencies.py        # FastAPI dependencies
│   │   └── schemas.py             # Pydantic models
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── core.py                # MLPipeline class
│   │   ├── stages.py              # Individual stage implementations
│   │   └── result.py              # PipelineResult dataclass
│   ├── models/
│   │   ├── __init__.py
│   │   ├── manager.py             # ModelManager class
│   │   ├── loader.py              # Model loading utilities
│   │   └── registry.py            # Model registry management
│   ├── features/
│   │   ├── __init__.py
│   │   ├── extractor.py           # Feature extraction (77+96 dim)
│   │   ├── thermal.py             # Thermal preprocessing
│   │   └── transforms.py          # Feature transformations
│   ├── redis/
│   │   ├── __init__.py
│   │   ├── consumer.py            # Redis Streams consumer
│   │   └── producer.py            # Result publisher
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # Settings class
│       ├── logging.py             # Logging configuration
│       └── metrics.py             # Prometheus metrics
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_api.py                # API endpoint tests
│   ├── test_pipeline.py           # Pipeline integration tests
│   ├── test_stages.py             # Individual stage tests
│   ├── test_features.py           # Feature extraction tests
│   ├── test_models.py             # Model loading tests
│   └── integration/
│       ├── __init__.py
│       └── test_redis_streams.py  # Redis integration tests
│
├── scripts/
│   ├── setup_models.py            # Model setup (production)
│   ├── export_models.py           # Export to ONNX/CoreML
│   ├── validate_models.py         # Model validation
│   ├── generate_sample_images.py  # Test image generation
│   └── train/
│       ├── train_stage1.py        # Stage 1 training
│       ├── train_stage2.py        # Stage 2 training
│       ├── train_stage3.py        # Stage 3 training
│       └── train_stage4.py        # Stage 4 training
│
├── demo/
│   ├── __init__.py
│   ├── run_demo.py                # Demo pipeline
│   ├── demo_server.py             # Demo HTTP server
│   ├── setup_demo_models.py       # Demo model setup
│   └── outputs/                   # Demo results
│
├── docs/
│   ├── README.md                  → Main documentation
│   ├── ARCHITECTURE.md            → Complete architecture
│   ├── TRAINING.md                → Training guide
│   ├── DEPLOYMENT.md              → Deployment procedures
│   ├── THERMAL.md                 → Thermal camera support
│   └── archive/                   → Historical docs
│
├── models/                        → Model storage (gitignored)
│   ├── registry.json
│   └── stage{1-4}/
│
├── .venv/                         → Virtual environment (gitignored)
├── .gitignore
├── pyproject.toml                 → Primary dependencies
├── requirements.txt               → Pip compatibility
├── Dockerfile
└── README.md                      → Quick start guide
```

---

## 2. Code Modernization

### 2.1 Package Structure

**Current Issue:** All modules in root directory creates import conflicts and poor organization.

**Solution:** Restructure into proper Python package with `src/` layout.

```python
# Before
from pipeline import MLPipeline
from features import extract_features
from thermal_utils import preprocess_thermal

# After
from ml_inference.pipeline import MLPipeline
from ml_inference.features import extract_features
from ml_inference.utils.thermal import preprocess_thermal
```

### 2.2 Configuration Management

**Current Issue:** Settings scattered across files, no validation.

**Solution:** Centralized configuration with Pydantic Settings.

```python
# src/utils/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class MLServiceSettings(BaseSettings):
    """ML Service configuration."""
    
    # Service
    service_name: str = "ml-inference"
    host: str = "0.0.0.0"
    port: int = 8001
    workers: int = 1
    
    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_stream: str = "thermal:calibrated"
    
    # Models
    model_path: Path = Path("/app/models")
    model_registry: str = "registry.json"
    device: Literal["edge", "cloud"] = "edge"
    
    # Inference
    batch_size: int = Field(default=8, ge=1, le=32)
    inference_timeout_ms: int = 35
    confidence_threshold: float = 0.65
    
    # Monitoring
    enable_metrics: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    class Config:
        env_prefix = "ML_"
        env_file = ".env"
    
    @validator("model_path")
    def validate_model_path(cls, v):
        if not v.exists():
            raise ValueError(f"Model path does not exist: {v}")
        return v
```

### 2.3 Error Handling

**Current Issue:** Inconsistent error handling, generic exceptions.

**Solution:** Custom exception hierarchy with proper error codes.

```python
# src/utils/exceptions.py
class MLServiceError(Exception):
    """Base exception for ML service."""
    def __init__(self, message: str, code: str, status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class ModelNotFoundError(MLServiceError):
    def __init__(self, model_name: str):
        super().__init__(
            message=f"Model not found: {model_name}",
            code="MODEL_NOT_FOUND",
            status_code=404
        )

class InferenceTimeoutError(MLServiceError):
    def __init__(self, timeout_ms: int):
        super().__init__(
            message=f"Inference timed out after {timeout_ms}ms",
            code="INFERENCE_TIMEOUT",
            status_code=504
        )

class ThermalParserError(MLServiceError):
    def __init__(self, camera_type: str, detail: str):
        super().__init__(
            message=f"Thermal parsing failed for {camera_type}: {detail}",
            code="THERMAL_PARSER_ERROR",
            status_code=400
        )
```

### 2.4 Logging Standardization

**Current Issue:** Inconsistent logging format, missing context.

**Solution:** Structured JSON logging with correlation IDs.

```python
# src/utils/logging.py
import logging
import json
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra context
        if hasattr(record, "module_id"):
            log_entry["module_id"] = record.module_id
        if hasattr(record, "inspection_id"):
            log_entry["inspection_id"] = record.inspection_id
        if hasattr(record, "processing_time_ms"):
            log_entry["processing_time_ms"] = record.processing_time_ms
            
        return json.dumps(log_entry)

def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    logger = logging.getLogger("ml_inference")
    logger.setLevel(getattr(logging, level))
    logger.addHandler(handler)
```

---

## 3. Testing Strategy

### 3.1 Current State

- **Location:** `tests/test_ml_service.py`
- **Coverage:** Unknown (no coverage report)
- **Type:** Mixed unit/integration tests
- **Fixtures:** Minimal

### 3.2 Target State

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from ml_inference.main import app
from ml_inference.pipeline import MLPipeline

@pytest.fixture
def client():
    """Test client for API endpoints."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def pipeline():
    """Initialized ML pipeline."""
    return MLPipeline(model_path="tests/fixtures/models")

@pytest.fixture
def sample_thermal_image():
    """Sample thermal image for testing."""
    return load_test_image("tests/images/sample.rjpeg")
```

**Test Categories:**

| Category | Location | Coverage Target |
|----------|----------|-----------------|
| Unit Tests | `tests/unit/` | 80%+ |
| Integration Tests | `tests/integration/` | Critical paths |
| E2E Tests | `tests/e2e/` | Full pipeline |
| Performance Tests | `tests/perf/` | Latency benchmarks |

### 3.3 Pytest Configuration

```ini
# tests/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --strict-markers
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    requires_gpu: Tests requiring GPU
```

---

## 4. Docker Optimization

### 4.1 Current State

✅ Multi-stage build  
✅ uv package manager  
✅ Health checks  
⚠️ Large image size (estimated ~1.5GB)  
⚠️ No GPU variant  

### 4.2 Improvements

#### Base Image Optimization

```dockerfile
# Use slim base
FROM python:3.11-slim-bookworm

# Install only required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

#### GPU Variant

```dockerfile
# Dockerfile.gpu
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Install Python
RUN apt-get update && apt-get install -y python3.11 python3.11-venv

# Install TensorRT for GPU acceleration
RUN pip install tensorrt onnxruntime-gpu
```

#### Build Arguments

```dockerfile
ARG PYTHON_VERSION=3.11
ARG UV_VERSION=latest
ARG MODEL_SOURCE=local

# Use in build
FROM python:${PYTHON_VERSION}-slim
```

---

## 5. Performance Optimization

### 5.1 Model Loading

**Current:** Models loaded on startup  
**Issue:** Cold start latency, memory pressure  
**Solution:** Lazy loading with LRU cache

```python
from functools import lru_cache
from pathlib import Path

class ModelManager:
    @lru_cache(maxsize=4)
    def load_model(self, stage: int) -> Any:
        """Load model with LRU caching."""
        model_path = self.model_registry.get_model_path(stage)
        return self._load_model_file(model_path)
    
    def preload_models(self, stages: List[int] = None):
        """Preload models for specified stages."""
        if stages is None:
            stages = [1, 2, 3, 4]
        for stage in stages:
            self.load_model(stage)
```

### 5.2 Batch Processing

**Current:** Fixed batch size  
**Solution:** Dynamic batching with timeout

```python
class BatchProcessor:
    def __init__(self, max_batch_size: int = 8, max_wait_ms: int = 10):
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.batch_queue = asyncio.Queue()
    
    async def process_batch(self):
        """Process batch with dynamic sizing."""
        batch = []
        start_time = time.time()
        
        while len(batch) < self.max_batch_size:
            try:
                remaining_ms = self.max_wait_ms - (time.time() - start_time) * 1000
                if remaining_ms <= 0:
                    break
                    
                item = await asyncio.wait_for(
                    self.batch_queue.get(),
                    timeout=remaining_ms / 1000
                )
                batch.append(item)
            except asyncio.TimeoutError:
                break
        
        if batch:
            await self._run_inference(batch)
```

### 5.3 Memory Management

**Issue:** Model weights consume significant memory  
**Solution:** Model quantization and pruning

```python
# Use INT8 quantization for edge deployment
import coremltools as ct

quantized_model = ct.models.neural_network.quantization_utils.quantize_weights(
    model,
    nbits=8
)
```

---

## 6. Monitoring & Observability

### 6.1 Metrics (Prometheus)

```python
# src/utils/metrics.py
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge

# Metrics definitions
INFERENCE_COUNTER = Counter(
    "ml_inference_total",
    "Total number of inferences",
    ["stage", "defect_type", "severity"]
)

INFERENCE_LATENCY = Histogram(
    "ml_inference_latency_seconds",
    "Inference latency",
    ["stage"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

MODEL_INFO = Gauge(
    "ml_model_info",
    "Model version and metadata",
    ["stage", "version", "format"]
)

ACTIVE_MODELS = Gauge(
    "ml_active_models",
    "Number of active models in memory"
)

def setup_metrics(app):
    """Configure Prometheus metrics."""
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

### 6.2 Distributed Tracing

**Future:** OpenTelemetry integration for tracing across services

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Configure tracer
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({"service.name": "ml-inference"})
    )
)
tracer = trace.get_tracer(__name__)
```

---

## 7. Implementation Timeline

### Phase 1: Cleanup (Week 1)

| Task | Priority | Estimated Time |
|------|----------|----------------|
| Archive redundant docs | High | 2 hours |
| Move demo files to `demo/` | High | 1 hour |
| Delete obsolete notebooks | High | 30 min |
| Consolidate requirements | Medium | 1 hour |
| Update README.md | High | 2 hours |

### Phase 2: Restructure (Week 2)

| Task | Priority | Estimated Time |
|------|----------|----------------|
| Create `src/` package structure | High | 4 hours |
| Move and update imports | High | 3 hours |
| Update Dockerfile | High | 2 hours |
| Update tests for new structure | High | 3 hours |
| Verify all functionality | High | 4 hours |

### Phase 3: Modernization (Week 3)

| Task | Priority | Estimated Time |
|------|----------|----------------|
| Implement centralized config | High | 3 hours |
| Add custom exceptions | Medium | 2 hours |
| Implement structured logging | High | 3 hours |
| Add Prometheus metrics | Medium | 3 hours |

### Phase 4: Testing (Week 4)

| Task | Priority | Estimated Time |
|------|----------|----------------|
| Add pytest fixtures | High | 2 hours |
| Write unit tests | High | 8 hours |
| Write integration tests | High | 6 hours |
| Add coverage reporting | Medium | 2 hours |
| Achieve 80%+ coverage | High | 4 hours |

### Phase 5: Optimization (Week 5)

| Task | Priority | Estimated Time |
|------|----------|----------------|
| Implement lazy model loading | Medium | 3 hours |
| Add dynamic batching | Medium | 4 hours |
| Optimize Docker image | Medium | 3 hours |
| Create GPU variant | Low | 4 hours |

---

## 8. Success Criteria

### Code Quality
- [ ] All code in `src/` package structure
- [ ] Type hints on all public functions
- [ ] Docstrings for all public classes/functions
- [ ] No circular imports

### Testing
- [ ] 80%+ code coverage
- [ ] All tests passing in CI
- [ ] Performance tests under latency budget

### Documentation
- [ ] Single README.md with quick start
- [ ] Architecture reference complete
- [ ] API documentation auto-generated
- [ ] Deployment guide complete

### Performance
- [ ] <35ms latency (Mac M2)
- [ ] <15ms latency (GPU cloud)
- [ ] Memory usage <2GB
- [ ] Docker image <1GB

### Operations
- [ ] Health checks working
- [ ] Metrics exposed at `/metrics`
- [ ] Structured logging enabled
- [ ] Graceful shutdown implemented

---

## 9. Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking changes during refactor | High | Medium | Comprehensive test suite before refactor |
| Performance regression | High | Low | Benchmark before/after each change |
| Model loading failures | Critical | Low | Keep backup models, rollback plan |
| Docker build failures | Medium | Low | Test builds at each stage |
| Import errors | Medium | Medium | Incremental refactoring with verification |

---

## 10. Next Steps

1. **Immediate:** Review and approve this plan
2. **Day 1:** Create backup branch
3. **Day 2-3:** Execute Phase 1 (Cleanup)
4. **Day 4-5:** Begin Phase 2 (Restructure)
5. **Week 2:** Complete restructuring, start testing
6. **Week 3-4:** Testing and modernization
7. **Week 5:** Optimization and documentation

---

## Appendix A: Quick Reference Commands

### Cleanup Commands
```bash
# Archive old docs
mkdir -p docs/archive
mv ML_IMPLEMENTATION.md docs/archive/
mv ML_LIFECYCLE.md docs/archive/
# ... etc

# Move demo files
mkdir -p demo
mv demo_*.py demo/
mv setup_demo_models.py demo/

# Delete notebooks
rm Doctor_Doom_ML_Training*.ipynb
```

### Restructure Commands
```bash
# Create package structure
mkdir -p src/{api,pipeline,models,features,redis,utils}
mkdir -p tests/{unit,integration,e2e,perf}

# Move files
mv main.py src/
mv pipeline.py src/pipeline/core.py
mv features.py src/features/extractor.py
mv thermal_utils.py src/features/thermal.py
mv model_manager.py src/models/manager.py
mv redis_streams.py src/redis/consumer.py
```

### Test Commands
```bash
# Run all tests
uv run pytest tests/ -v --cov=src --cov-report=html

# Run specific test category
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v -m "not slow"

# Generate coverage report
uv run pytest --cov=src --cov-report=term-missing --cov-report=xml
```

---

**Document Owner:** ML Team  
**Review Date:** 2026-03-20  
**Next Review:** After Phase 2 completion
