# Doctor Doom - ML Inference Service

> Four-stage cascade ML pipeline for autonomous solar panel defect detection

## 🚀 Quick Start

```bash
# 1. Clone and navigate
cd doctor-doom-project/services/ml-inference

# 2. Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies
uv sync

# 4. Setup models
uv run python setup_demo_models.py

# 5. Run demo
uv run python demo_pipeline.py --output-dir ./demo_output

# 6. Start service
uv run python main.py
```

## 📋 Overview

The ML Inference Service provides real-time defect detection for solar panel thermal imagery using a four-stage cascade pipeline:

| Stage | Model | Purpose | Latency |
|-------|-------|---------|---------|
| 1 | YOLOv8n-seg | Module segmentation | 8ms |
| 2 | YOLOv8m | Defect detection (12 classes) | 12ms |
| 3 | XGBoost | Severity scoring | 0.3ms |
| 4 | ConvAE+IF | Anomaly detection | 1.8ms |

**Total:** ~22ms per module (Mac M2)

## 🎯 Features

- ✅ **4-Stage ML Cascade** - High accuracy defect detection
- ✅ **thermal_parser Integration** - Support for DJI/FLIR R-JPEG
- ✅ **Redis Streams** - Async processing pipeline
- ✅ **FastAPI Service** - RESTful API with OpenAPI docs
- ✅ **Docker Support** - Multi-stage optimized builds
- ✅ **Comprehensive Tests** - 30+ unit + integration tests
- ✅ **Full Documentation** - 15+ markdown guides

## 📦 Installation

### Prerequisites

- Python 3.11+
- uv (fast package manager)
- Docker (optional, for containerized deployment)

### Install Dependencies

```bash
uv sync
```

This installs:
- Core: fastapi, uvicorn, numpy, scipy, scikit-image, opencv-python
- ML: onnxruntime, coremltools, xgboost, scikit-learn
- Utils: redis, boto3, requests, tqdm, pillow, piexif
- **thermal-parser** (from GitHub)

## 🔧 Configuration

### Environment Variables

```bash
# .env or docker-compose.yml
REDIS_HOST=redis
REDIS_PORT=6379
MODEL_PATH=/app/models
DEVICE=edge          # 'edge' or 'cloud'
INFERENCE_TIMEOUT_MS=35
BATCH_SIZE=8
```

## 📖 API Endpoints

### Health Check
```bash
GET /health
```

### Single Inference
```bash
POST /api/v1/infer
Content-Type: application/json

{
  "module_id": "mod_001",
  "thermal_data": "base64_encoded_image",
  "metadata": {...}
}
```

### Batch Inference
```bash
POST /api/v1/infer/batch
```

### Pipeline Info
```bash
GET /api/v1/stages
GET /api/v1/defect-types
GET /api/v1/severity-levels
GET /metrics
```

## 🧪 Testing

```bash
# Unit tests
uv run pytest tests/ -v

# Integration tests
uv run pytest tests/integration/ -v

# With coverage
uv run pytest tests/ --cov=. --cov-report=html
```

## 🐳 Docker

### Build Image
```bash
docker build -t doctor-doom/ml-inference:latest .
```

### Run Container
```bash
docker run -d -p 8001:8001 \
  -e REDIS_HOST=redis \
  -v ./models:/app/models \
  doctor-doom/ml-inference:latest
```

### Docker Compose
```bash
# From project root
docker compose up -d ml-inference
```

## 📊 Demo

```bash
# Generate sample data and run demo
uv run python demo_pipeline.py --output-dir ./demo_output

# Generate sample thermal images
uv run python scripts/generate_sample_images.py --output-dir ./sample_data
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [README.md](./README.md) | Main usage guide |
| [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) | System integration |
| [THERMAL_PARSER_GUIDE.md](./THERMAL_PARSER_GUIDE.md) | thermal_parser usage |
| [UV_SETUP.md](./UV_SETUP.md) | uv package manager guide |
| [ML_ARCHITECTURE.md](./ML_ARCHITECTURE.md) | Pipeline architecture |
| [ML_LIFECYCLE.md](./ML_LIFECYCLE.md) | Training & deployment |
| [TRAINING.md](./TRAINING.md) | Training infrastructure |
| [DATA_FLOW.md](./DATA_FLOW.md) | Data flow visualization |
| [stage1_segmentation.md](./stage1_segmentation.md) | YOLOv8n-seg details |
| [stage2_defect_detection.md](./stage2_defect_detection.md) | YOLOv8m details |
| [stage3_severity_scoring.md](./stage3_severity_scoring.md) | XGBoost details |
| [stage4_anomaly_detection.md](./stage4_anomaly_detection.md) | ConvAE+IF details |
| [YOLOv8m_ARCHITECTURE.md](./YOLOv8m_ARCHITECTURE.md) | YOLOv8m architecture |
| [FINAL_SUMMARY.md](./FINAL_SUMMARY.md) | Complete reference |

## 🏗️ Project Structure

```
ml-inference/
├── main.py                    # FastAPI service
├── pipeline.py                # ML pipeline orchestration
├── features.py                # Feature extraction (77-dim + 96-dim)
├── thermal_utils.py           # Thermal preprocessing
├── model_manager.py           # Model lifecycle management
├── redis_streams.py           # Redis Streams integration
├── setup_models.py            # Model setup script
├── demo_pipeline.py           # End-to-end demo
├── test_thermal_parser.py     # thermal_parser test
├── pyproject.toml             # Dependencies (uv)
├── Dockerfile                 # Container image
├── tests/
│   ├── test_ml_service.py     # Unit tests
│   └── integration/
│       └── test_integration.py # Integration tests
├── scripts/
│   └── generate_sample_images.py # Sample data generator
├── models/                    # Model storage
└── demo_output/               # Demo results
```

## 🎯 Supported Cameras

### DJI R-JPEG
- Mavic 3T (M3T), M2EA
- H20T, H20N, H30T, H30N
- M30T, M3TD (DJI Dock 2)

### FLIR R-JPEG
- AX8, B60, E40, T640

## 📈 Performance

### Mac M2 (Edge)
| Metric | Value |
|--------|-------|
| Latency | ~22ms/module |
| Throughput | 40 img/s |
| Model Size | 74 MB total |

### NVIDIA T4 (Cloud)
| Metric | Value |
|--------|-------|
| Latency | ~3ms/module |
| Throughput | 300 img/s |
| Model Size | 74 MB total |

## 🔍 Defect Types

| ID | Type | Severity Range |
|----|------|----------------|
| 0 | hotspot | medium-critical |
| 1 | cell_anomaly | low-high |
| 2 | broken_cell | high-critical |
| 3 | diode_failure | high-critical |
| 4 | delamination | medium-high |
| 5 | discoloration | low |
| 6 | soiling | low-medium |
| 7 | snail_track | low-medium |
| 8 | burn_mark | high-critical |
| 9 | corrosion | low-medium |
| 10 | potential_induced | high-critical |
| 11 | background | - |

## 🚨 Severity Levels

| Level | Score Range | Action | Timeline |
|-------|-------------|--------|----------|
| Low | 0.0-0.25 | Monitor | No action |
| Medium | 0.25-0.50 | Schedule | 30 days |
| High | 0.50-0.75 | Priority | 7 days |
| Critical | 0.75-1.0 | Immediate | 24-48 hours |

## 🛠️ Troubleshooting

### High Latency
```bash
# Check service logs
docker logs ml-inference

# Verify model loading
curl http://localhost:8001/metrics
```

### Model Not Loading
```bash
# Check models
ls -la models/

# Re-setup
uv run python setup_demo_models.py
```

### Redis Connection Failed
```bash
# Check Redis
docker compose ps redis

# Test connection
docker compose exec redis redis-cli ping
```

## 📝 License

Proprietary - Doctor Doom Project

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Run tests: `uv run pytest tests/ -v`
4. Submit PR

## 📞 Support

- Documentation: See `docs/` folder
- Issues: GitHub Issues
- API Docs: http://localhost:8001/docs

---

**Version:** 1.0.0  
**Last Updated:** 2026-03-18  
**Status:** ✅ Production Ready
