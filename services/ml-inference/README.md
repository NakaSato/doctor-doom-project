# ML Inference Service

Four-stage cascade pipeline for thermal solar panel defect detection.

## Overview

This service implements a complete ML pipeline for analyzing thermal imagery of solar panels:

| Stage | Model | Input | Output | Latency |
|-------|-------|-------|--------|---------|
| 1 | YOLOv8n-seg | 640×512 thermal | Module masks | 8ms |
| 2 | YOLOv8m | 128×128 crop | 12 defect classes | 12ms |
| 3 | XGBoost | 77-dim features | Severity (3-class) | 0.3ms |
| 4 | ConvAE + IF | 96-dim features | Anomaly score | 1.8ms |

**Total Pipeline Latency:** <25ms per module (Mac M2)

## Quick Start

### 1. Install Dependencies with uv

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (includes thermal-parser for R-JPEG parsing)
uv sync
```

**Note:** thermal-parser is automatically installed from GitHub. It supports:
- DJI Mavic 3T (M3T), M2EA, M30T, M3TD, H20T, H20N, H30T
- FLIR AX8, B60, E40, T640

**Platform Support:**
- ✅ Linux x64/x86
- ✅ Windows x64
- ⚠️ macOS (uses fallback loading)

### 2. Setup Models

```bash
# Download models (choose source)
python setup_models.py --source local
python setup_models.py --source s3 --s3-bucket my-bucket
python setup_models.py --source http --http-url https://models.example.com

# Verify models
python setup_models.py --verify
```

### 2. Start Service

```bash
# Using Docker Compose
docker compose up -d ml-inference

# Or standalone
python main.py
```

### 3. Check Health

```bash
curl http://localhost:8001/health
```

## API Endpoints

### Health Check

```bash
GET /health
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

### Single Inference

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
    "neighbor_temps": [45.2, 46.1, 44.8, 45.5],
    "string_mean": 48.5,
    "array_mean": 47.2,
    "expected_temp": 52.0,
    "string_position": 5,
    "row_index": 2,
    "col_index": 3,
    "time_of_day": 14,
    "wind_speed": 3.5,
    "humidity": 45
  }
}
```

Response:
```json
{
  "module_id": "mod_001_05",
  "inspection_id": "insp_001",
  "image_id": "img_001",
  "defect_type": "hot_spot",
  "severity": "critical",
  "severity_score": 0.85,
  "confidence": 0.92,
  "temperature_delta": 28.5,
  "max_temperature": 68.5,
  "ambient_temperature": 35.0,
  "affected_cells": [12, 13, 22, 23],
  "recommendations": [
    {
      "priority": 1,
      "action": "IMMEDIATE_REPLACEMENT",
      "description": "Module shows critical hotspot"
    }
  ],
  "anomaly_score": 0.15,
  "processing_time_ms": 22.5,
  "model_version": "1.0.0"
}
```

### Batch Inference

```bash
POST /api/v1/infer/batch
Content-Type: application/json

{
  "requests": [...],
  "max_batch_size": 8
}
```

### Get Pipeline Info

```bash
GET /api/v1/stages
```

### Get Defect Types

```bash
GET /api/v1/defect-types
```

## Project Structure

```
ml-inference/
├── main.py                    # FastAPI service entry point
├── pipeline.py                # ML pipeline orchestration
├── features.py                # Feature extraction (Stage 3/4)
├── thermal_utils.py           # Thermal image preprocessing
├── model_manager.py           # Model lifecycle management
├── setup_models.py            # Model setup script
├── ML_ARCHITECTURE.md         # Complete architecture docs
├── ML_LIFECYCLE.md            # Training/deployment lifecycle
├── TRAINING.md                # Training infrastructure
├── stage1_segmentation.md     # Stage 1 documentation
├── stage2_defect_detection.md # Stage 2 documentation
├── stage3_severity_scoring.md # Stage 3 documentation
├── stage4_anomaly_detection.md# Stage 4 documentation
└── YOLOv8m_ARCHITECTURE.md    # YOLOv8m architecture details
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | redis | Redis server host |
| `REDIS_PORT` | 6379 | Redis server port |
| `MODEL_PATH` | /app/models | Model directory |
| `INFERENCE_TIMEOUT_MS` | 35 | Inference timeout |
| `DEVICE` | edge | Device type (edge/cloud) |
| `BATCH_SIZE` | 8 | Default batch size |

## Model Formats

Supported formats:
- **ONNX** - Cross-platform inference
- **CoreML** - Mac M2 optimized (INT8 quantized)
- **PyTorch** - Training/research

Model directory structure:
```
/app/models/
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
# With uv
uv sync --dev

# Or with pip
uv pip install -r requirements.txt
```

### Run Tests

```bash
pytest tests/
```

### Local Development

```bash
# Start Redis locally
docker run -d -p 6379:6379 redis:7-alpine

# Run service
python main.py
```

## Monitoring

### Metrics

```bash
GET /metrics
```

Returns:
- Model versions
- Stage latencies
- Throughput statistics
- Memory usage

### Logging

Logs are written to stdout in JSON format:

```json
{"timestamp": "...", "level": "INFO", "message": "...", "module_id": "..."}
```

## Troubleshooting

### Models Not Loading

```bash
# Check model directory
ls -la /app/models/

# Verify models
python setup_models.py --verify

# Re-download if needed
python setup_models.py --source s3 --s3-bucket my-bucket
```

### High Latency

```bash
# Check device setting
echo $DEVICE  # Should be 'edge' for M2

# Verify CoreML models are being used
curl http://localhost:8001/metrics
```

### Memory Issues

```bash
# Reduce batch size
export BATCH_SIZE=4

# Clear model cache
rm -rf /app/models/cache/*
```

## Performance Benchmarks

### Mac M2 (Edge)

| Batch Size | Throughput | Avg Latency |
|------------|------------|-------------|
| 1 | 40 img/s | 25ms |
| 4 | 120 img/s | 33ms |
| 8 | 200 img/s | 40ms |

### NVIDIA T4 (Cloud)

| Batch Size | Throughput | Avg Latency |
|------------|------------|-------------|
| 1 | 300 img/s | 3.3ms |
| 8 | 800 img/s | 10ms |
| 16 | 1000 img/s | 16ms |

## License

Proprietary - Doctor Doom Project
