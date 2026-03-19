# ML Service Demo - End-to-End Integration

## Quick Start

### Option 1: Run Demo Server (Recommended for Testing)

```bash
cd services/ml-inference

# Install dependencies
uv sync

# Start demo server
uv run python demo_server.py --port 8001
```

### Option 2: Run Full Backend with Docker

```bash
# From project root
docker compose up -d ml-inference api-gateway redis
```

---

## Testing the Integration

### 1. Test Health Check

```bash
curl http://localhost:8001/health

# Expected response:
# {"status":"healthy","service":"ml-inference-demo",...}
```

### 2. Test Single Inference

```bash
curl -X POST http://localhost:8001/api/v1/ml/infer \
  -H "Content-Type: application/json" \
  -d '{
    "module_id": "mod_001",
    "inspection_id": "insp_001",
    "image_id": "img_001",
    "thermal_data": "'$(python3 -c "import base64; import numpy as np; data = np.random.randn(640*512).astype(np.float32); print(base64.b64encode(data.tobytes()).decode())")'",
    "metadata": {"ambient_temp": 35.0}
  }'
```

### 3. Test Frontend Connection

```bash
# Start frontend
cd frontend
npm run dev

# Open browser to http://localhost:3000/inspector
```

---

## Demo Server Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/metrics` | GET | Service metrics |
| `/api/v1/ml/stages` | GET | Pipeline information |
| `/api/v1/ml/defect-types` | GET | Supported defect types |
| `/api/v1/ml/severity-levels` | GET | Severity definitions |
| `/api/v1/ml/infer` | POST | Single inference |
| `/api/v1/ml/infer/batch` | POST | Batch inference |

---

## Frontend Configuration

Create `frontend/.env`:

```bash
VITE_API_URL=http://localhost:8001/api/v1
VITE_ML_SERVICE_URL=http://localhost:8001
```

---

## Testing with Real Thermal Images

### 1. Convert Image to Base64

```python
import base64
import numpy as np

# Load thermal image (numpy array)
thermal_data = np.load('thermal_image.npy')

# Convert to base64
b64_data = base64.b64encode(thermal_data.tobytes()).decode()

print(f"Base64 length: {len(b64_data)}")
```

### 2. Send to API

```python
import requests

response = requests.post(
    'http://localhost:8001/api/v1/ml/infer',
    json={
        'module_id': 'mod_001',
        'inspection_id': 'insp_001',
        'image_id': 'img_001',
        'thermal_data': b64_data,
        'metadata': {'ambient_temp': 35.0}
    }
)

result = response.json()
print(f"Defect: {result['defect_type']}")
print(f"Severity: {result['severity']}")
print(f"Confidence: {result['confidence']:.1%}")
```

---

## Expected Response Format

```json
{
  "module_id": "mod_001",
  "inspection_id": "insp_001",
  "image_id": "img_001",
  "defect_type": "hotspot",
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
      "description": "Module shows critical hotspot",
      "estimated_power_loss": "15-20%",
      "safety_risk": "Fire hazard"
    }
  ],
  "anomaly_score": 0.15,
  "processing_time_ms": 25.3,
  "model_version": "1.0.0",
  "timestamp": "2026-03-18T10:30:00Z"
}
```

---

## Performance Benchmarks

### Demo Server

| Metric | Value |
|--------|-------|
| Single Inference | ~25ms |
| Batch (8 images) | ~200ms |
| Requests/sec | ~40 |

### Production (with real models)

| Metric | Value |
|--------|-------|
| Single Inference | ~22ms (M2) |
| Batch (8 images) | ~100ms |
| Requests/sec | ~45 |

---

## Troubleshooting

### "Failed to fetch" Error

**Cause:** Server not running or CORS issue

**Solution:**
```bash
# Check server is running
curl http://localhost:8001/health

# Check CORS in demo_server.py
# Should have: allow_origins=["*"]
```

### High Latency

**Cause:** Server overloaded or network issue

**Solution:**
```bash
# Check server logs
# Look for slow requests

# Test locally
curl http://localhost:8001/health
```

### Frontend Can't Connect

**Cause:** Wrong API URL

**Solution:**
```bash
# Check .env file
cat frontend/.env

# Should have:
# VITE_API_URL=http://localhost:8001/api/v1
```

---

## Integration Test Script

```bash
# Run automated integration tests
uv run python tests/integration/test_api.py
```

---

## Next Steps

1. **Test with frontend** - Open `http://localhost:3000/inspector`
2. **Upload thermal images** - Use the Upload tab
3. **View analysis results** - Check Array Map and Defect Log tabs
4. **Generate report** - Use the Report tab

---

## Resources

- [Frontend Integration Guide](../../frontend/src/views/ml-analysis/INTEGRATION_GUIDE.md)
- [ML Service README](README.md)
- [Training Setup](TRAINING_SETUP.md)
- [API Documentation](../../API.md)

---

**Status:** ✅ Ready for Testing  
**Version:** 1.0.0  
**Last Updated:** 2026-03-18
