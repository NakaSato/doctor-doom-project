# ML Service Integration Guide

## Overview

This guide shows how to integrate the ML Inference Service with the Doctor Doom system.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Doctor Doom System                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   API       │────▶│   ML        │
│   (React)   │     │   Gateway   │     │   Inference │
│   :3000     │     │   :8000     │     │   :8001     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Redis     │◀────│   Redis     │
                    │   Streams   │     │   Streams   │
                    └─────────────┘     └─────────────┘
```

## Integration Points

### 1. API Gateway Integration

The API Gateway routes ML requests to the ML service:

```yaml
# docker-compose.yml
api-gateway:
  environment:
    - ML_INFERENCE_URL=http://ml-inference:8001

ml-inference:
  ports:
    - "8001:8001"
  environment:
    - REDIS_HOST=redis
```

### 2. Frontend Integration

React components call the ML service through the API Gateway:

```typescript
// frontend/src/services/ml.ts
const API_BASE = '/api/v1';

export async function analyzeModule(
  moduleId: string,
  thermalData: string,
  metadata: Metadata
): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE}/ml/infer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      module_id: moduleId,
      thermal_data: thermalData,
      metadata: metadata
    })
  });
  
  return response.json();
}
```

### 3. Redis Streams Integration

Async processing through Redis Streams:

```python
# Producer (API Gateway)
await redis.xadd(
    "thermal:calibrated",
    {"data": json.dumps(image_data)}
)

# Consumer (ML Service)
messages = await redis.xreadgroup(
    groupname="ml-inference",
    consumername="ml-consumer-1",
    streams={"thermal:calibrated": ">"},
    count=1
)

# Result
await redis.xadd(
    "defect:detected",
    {"data": json.dumps(analysis_result)}
)
```

## Usage Examples

### Direct API Call

```bash
curl -X POST http://localhost:8001/api/v1/infer \
  -H "Content-Type: application/json" \
  -d '{
    "module_id": "mod_001_05",
    "inspection_id": "insp_001",
    "image_id": "img_001",
    "thermal_data": "base64_encoded_image",
    "metadata": {
      "ambient_temp": 35.0,
      "irradiance": 850
    }
  }'
```

### Python Client

```python
import httpx
import base64
import numpy as np

async def analyze_thermal_image(image: np.ndarray):
    async with httpx.AsyncClient() as client:
        # Encode image
        thermal_data = base64.b64encode(image.tobytes()).decode()
        
        # Call API
        response = await client.post(
            "http://localhost:8001/api/v1/infer",
            json={
                "module_id": "mod_001",
                "thermal_data": thermal_data,
                "metadata": {"ambient_temp": 35.0}
            }
        )
        
        return response.json()
```

### JavaScript/TypeScript Client

```typescript
import axios from 'axios';

interface AnalysisResult {
  module_id: string;
  defect_type: string;
  severity: string;
  confidence: number;
  temperature_delta: number;
}

async function analyzeModule(
  thermalData: Uint8Array,
  moduleId: string
): Promise<AnalysisResult> {
  // Convert to base64
  const base64Data = btoa(
    String.fromCharCode(...thermalData)
  );
  
  const response = await axios.post('/api/v1/ml/infer', {
    module_id: moduleId,
    thermal_data: base64Data,
    metadata: { ambient_temp: 35.0 }
  });
  
  return response.data;
}
```

## Data Formats

### Request Format

```json
{
  "module_id": "mod_001_05",
  "inspection_id": "insp_001",
  "image_id": "img_001",
  "thermal_data": "base64_encoded_float32_array",
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

### Response Format

```json
{
  "module_id": "mod_001_05",
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
      "description": "Module shows critical hotspot"
    }
  ],
  "anomaly_score": 0.15,
  "processing_time_ms": 22.5,
  "model_version": "1.0.0",
  "timestamp": "2026-03-18T10:30:00Z"
}
```

## Error Handling

### Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": "INFERENCE_FAILED",
    "message": "Failed to process thermal image",
    "details": "Invalid image dimensions"
  }
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid input) |
| 422 | Validation Error |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Performance Tuning

### Batch Processing

```python
# Process multiple modules at once
async def batch_analyze(modules: List[ModuleData]):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/v1/infer/batch",
            json={
                "requests": modules,
                "max_batch_size": 8
            }
        )
        return response.json()
```

### Streaming Results

```python
# For large batches, use streaming
async def stream_analyze(image_stream):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8001/api/v1/infer/stream",
            content=image_stream
        ) as response:
            async for line in response.aiter_lines():
                yield json.loads(line)
```

## Monitoring

### Health Check

```bash
curl http://localhost:8001/health

# Response:
# {"status": "healthy", "service": "ml-inference", ...}
```

### Metrics

```bash
curl http://localhost:8001/metrics

# Returns:
# - Model versions
# - Stage latencies
# - Throughput statistics
```

### Logging

Logs are in JSON format:

```json
{"timestamp": "...", "level": "INFO", "message": "Processed module", "module_id": "mod_001", "defect_type": "hotspot"}
```

## Testing

### Unit Tests

```bash
cd services/ml-inference
uv run pytest tests/ -v
```

### Integration Tests

```bash
# Start services
docker compose up -d ml-inference

# Run integration tests
uv run pytest tests/integration/ -v
```

### Load Testing

```bash
# Using locust
locust -f tests/load_test.py --host=http://localhost:8001
```

## Deployment

### Docker Compose

```yaml
# docker-compose.yml
services:
  ml-inference:
    build: ./services/ml-inference
    ports:
      - "8001:8001"
    environment:
      - REDIS_HOST=redis
      - MODEL_PATH=/app/models
      - DEVICE=edge
    volumes:
      - ./models:/app/models
    restart: unless-stopped
```

### Kubernetes

```yaml
# ml-inference-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-inference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ml-inference
  template:
    spec:
      containers:
      - name: ml-inference
        image: doctor-doom/ml-inference:latest
        ports:
        - containerPort: 8001
        env:
        - name: REDIS_HOST
          value: redis
        - name: MODEL_PATH
          value: /app/models
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
```

## Troubleshooting

### Common Issues

**Issue: High latency**
```bash
# Check service logs
docker logs ml-inference

# Check Redis connection
docker compose exec redis redis-cli ping

# Verify model loading
curl http://localhost:8001/metrics
```

**Issue: Model not loading**
```bash
# Check model directory
docker compose exec ml-inference ls -la /app/models/

# Re-setup models
docker compose exec ml-inference python setup_demo_models.py
```

**Issue: Redis connection failed**
```bash
# Check Redis is running
docker compose ps redis

# Check network
docker compose exec ml-inference ping redis
```

## Resources

- [ML Service README](./README.md)
- [API Documentation](../../API.md)
- [Architecture](../../ARCHITECTURE.md)
- [thermal_parser Guide](./THERMAL_PARSER_GUIDE.md)
