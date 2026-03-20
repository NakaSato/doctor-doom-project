# ML Inference Service

**Four-stage cascade pipeline for thermal solar panel defect detection**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

## Overview

This service implements a complete ML pipeline for analyzing thermal imagery from solar panel inspections. The four-stage cascade detects defects, classifies severity, and generates actionable recommendations.

| Stage | Model | Input | Output | Latency |
|-------|-------|-------|--------|---------|
| 1 | YOLOv8n-seg | 640×512 thermal | Module masks | 8ms |
| 2 | YOLOv8m | 128×128 crop | 12 defect classes | 12ms |
| 3 | XGBoost | 77-dim features | Severity (3-class) | 0.3ms |
| 4 | ConvAE + IF | 96-dim features | Anomaly score | 1.8ms |

**Total Pipeline Latency:** <25ms per module (Mac M2 CoreML)

## Quick Start

### Prerequisites

- Docker & Docker Compose (for containerized deployment)
- Python 3.11+ (for local development)
- uv package manager

### 1. Install Dependencies

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to service directory
cd services/ml-inference

# Install all dependencies (includes thermal-parser)
uv sync
```

**Thermal Camera Support:**
- ✅ DJI: Mavic 3T, M2EA, M30T, M3TD, H20T, H20N, H30T
- ✅ FLIR: AX8, B60, E40, T640

### 2. Setup Models

```bash
# Setup demo models (for testing)
uv run python setup_models.py --demo

# Or download production models
uv run python setup_models.py --source s3 --s3-bucket your-bucket

# Verify models
uv run python scripts/validate_models.py
```

### 3. Start Service

```bash
# Development (local)
uv run python main.py

# Or with uvicorn directly
uv run uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Docker (from project root)
docker compose up -d ml-inference
```

### 4. Verify Health

```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "service": "ml-inference",
  "version": "1.0.0",
  "device": "edge",
  "models_loaded": true,
  "stages": 4
}
```

## API Endpoints

### Health & Metrics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/metrics` | GET | Prometheus metrics |

### Inference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/infer` | POST | Single module inference |
| `/api/v1/infer/batch` | POST | Batch inference (up to 32) |

### Information

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/stages` | GET | Pipeline stage information |
| `/api/v1/defect-types` | GET | Supported defect types |
| `/api/v1/severity-levels` | GET | Severity classification levels |

### Example: Single Inference

```bash
POST /api/v1/infer
Content-Type: application/json

{
  "module_id": "mod_001_05",
  "inspection_id": "insp_001",
  "image_id": "img_001",
  "thermal_data": "base64_encoded_thermal_image",
  "metadata": {
    "ambient_temp": 35.0,
    "irradiance": 850,
    "neighbor_temps": [45.2, 46.1, 44.8, 45.5]
  }
}
```

Response:
```json
{
  "module_id": "mod_001_05",
  "defect_type": "hotspot",
  "severity": "critical",
  "severity_score": 0.85,
  "confidence": 0.92,
  "temperature_delta": 28.5,
  "affected_cells": [12, 13, 22, 23],
  "processing_time_ms": 22.5
}
```

## Project Structure

```
ml-inference/
├── main.py                      # FastAPI service entry point
├── pipeline.py                  # ML pipeline orchestration
├── features.py                  # Feature extraction (77+96 dim)
├── thermal_utils.py             # Thermal image preprocessing
├── model_manager.py             # Model lifecycle management
├── redis_streams.py             # Redis Streams consumer
│
├── setup_models.py              # Model setup script
├── export_models.py             # Export to ONNX/CoreML
│
├── demo/                        # Demo scripts & outputs
│   ├── run_demo.py
│   ├── demo_server.py
│   └── outputs/
│
├── scripts/                     # Training & utilities
│   ├── train/
│   │   ├── train_stage1.py
│   │   ├── train_stage2.py
│   │   ├── train_stage3.py
│   │   └── train_stage4.py
│   ├── export_models.py
│   ├── validate_models.py
│   └── generate_sample_images.py
│
├── tests/                       # Test suite
│   ├── test_ml_service.py
│   └── integration/
│
├── models/                      # Model storage (gitignored)
│   ├── registry.json
│   └── stage{1-4}/
│
├── docs/
│   ├── README.md                # This file
│   ├── ARCHITECTURE.md          # Complete architecture reference
│   ├── TRAINING.md              # Training guide
│   ├── DEPLOYMENT.md            # Deployment procedures
│   └── archive/                 # Historical documentation
│
├── pyproject.toml               # Dependencies (uv)
├── requirements.txt             # Dependencies (pip)
├── Dockerfile                   # Container image
└── CLEANUP_PLAN.md              # Modernization roadmap
```

## Configuration

Environment variables (set via `.env` or Docker):

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | redis | Redis server host |
| `REDIS_PORT` | 6379 | Redis server port |
| `MODEL_PATH` | /app/models | Model directory |
| `DEVICE` | edge | Device type (`edge`/`cloud`) |
| `INFERENCE_TIMEOUT_MS` | 35 | Inference timeout |
| `BATCH_SIZE` | 8 | Default batch size |
| `CONFIDENCE_THRESHOLD` | 0.65 | Detection threshold |

## Model Formats

**Supported Formats:**
- **ONNX** - Cross-platform inference (cloud)
- **CoreML** - Apple Silicon optimized (Mac M2 edge)
- **PyTorch** - Training/research

**Model Directory Structure:**
```
models/
├── registry.json
├── stage1/
│   ├── model.onnx
│   ├── model_coreml.mlpackage
│   └── model_info.json
├── stage2/
│   └── ...
├── stage3/
│   └── ...
└── stage4/
    └── ...
```

## Development

### Install Dependencies

```bash
# With uv (recommended)
uv sync --dev

# Or with pip
pip install -r requirements.txt
```

### Run Tests

```bash
# All tests
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ -v --cov=. --cov-report=html

# Specific test file
uv run pytest tests/test_ml_service.py -v
```

### Local Development

```bash
# Start Redis locally
docker run -d -p 6379:6379 --name redis-ml redis:7-alpine

# Run service with auto-reload
uv run uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Cleanup
docker stop redis-ml && docker rm redis-ml
```

## Docker Deployment

### Build Image

```bash
# From project root
docker build -t doctor-doom/ml-inference:latest ./services/ml-inference
```

### Run Container

```bash
docker run -d \
  -p 8001:8001 \
  -e REDIS_HOST=redis \
  -e MODEL_PATH=/app/models \
  -v ./models:/app/models \
  --name ml-inference \
  doctor-doom/ml-inference:latest
```

### Docker Compose (from project root)

```bash
docker compose up -d ml-inference
```

## Performance Benchmarks

### Mac M2 (Edge - CoreML)

| Batch Size | Throughput | Avg Latency | P99 Latency |
|------------|------------|-------------|-------------|
| 1 | 40 img/s | 25ms | 32ms |
| 4 | 120 img/s | 33ms | 41ms |
| 8 | 200 img/s | 40ms | 52ms |

### NVIDIA T4 (Cloud - TensorRT)

| Batch Size | Throughput | Avg Latency | P99 Latency |
|------------|------------|-------------|-------------|
| 1 | 300 img/s | 3.3ms | 5ms |
| 8 | 800 img/s | 10ms | 15ms |
| 16 | 1000 img/s | 16ms | 22ms |

## Monitoring

### Prometheus Metrics

Access metrics at `GET /metrics`:

- `ml_inference_total` - Total inference count
- `ml_inference_latency_seconds` - Latency histogram
- `ml_model_info` - Model version info
- `ml_active_models` - Loaded models count

### Structured Logging

Logs are JSON-formatted on stdout:

```json
{
  "timestamp": "2026-03-20T10:30:00Z",
  "level": "INFO",
  "logger": "ml_inference",
  "message": "Inference completed",
  "module_id": "mod_001_05",
  "processing_time_ms": 22.5
}
```

## Troubleshooting

### Models Not Loading

```bash
# Check model directory
ls -la models/

# Verify models
uv run python setup_models.py --verify

# Re-download if needed
uv run python setup_models.py --source s3 --s3-bucket your-bucket
```

### High Latency

```bash
# Check device setting (should be 'edge' for M2)
echo $DEVICE

# Verify CoreML models are being used
curl http://localhost:8001/metrics | grep model_format
```

### Memory Issues

```bash
# Reduce batch size
export BATCH_SIZE=4

# Clear model cache
rm -rf models/cache/*
```

### thermal-parser Issues (macOS)

On macOS, thermal-parser uses fallback loading (expected behavior). The service will still function correctly.

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Complete ML architecture reference |
| [TRAINING.md](docs/TRAINING.md) | Training infrastructure guide |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment procedures |
| [CLEANUP_PLAN.md](CLEANUP_PLAN.md) | Modernization roadmap |

## License

Proprietary - Doctor Doom Project

---

**Last Updated:** 2026-03-20  
**Version:** 1.0.0  
**Maintainer:** ML Team
