#!/usr/bin/env python3
"""
ML Service Integration Tests
============================

Integration tests for the complete ML inference pipeline.
Tests API endpoints, Redis Streams, and end-to-end workflows.

Usage:
    uv run pytest tests/integration/ -v
"""
import pytest
import asyncio
import httpx
import json
import base64
import numpy as np
from typing import Dict, Any
from pathlib import Path


# Test configuration
BASE_URL = "http://localhost:8001"
TIMEOUT = 30.0


@pytest.fixture
async def client():
    """Create async HTTP client."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
        yield client


@pytest.fixture
def sample_thermal_image() -> str:
    """Generate sample thermal image data (base64 encoded)."""
    # Create realistic thermal pattern
    image = np.random.normal(45, 8, (512, 640)).astype(np.float32)
    
    # Add hotspot
    image[200:250, 300:350] += 25
    
    # Encode as base64
    image_bytes = image.tobytes()
    return base64.b64encode(image_bytes).decode('utf-8')


@pytest.fixture
def sample_metadata() -> Dict[str, Any]:
    """Sample metadata for inference."""
    return {
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


class TestHealthEndpoints:
    """Test health and status endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "ml-inference"
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_metrics(self, client):
        """Test metrics endpoint."""
        response = await client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "model_version" in data
        assert "stages" in data
        assert "performance" in data
    
    @pytest.mark.asyncio
    async def test_stages_info(self, client):
        """Test pipeline stages info."""
        response = await client.get("/api/v1/stages")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "stages" in data
        assert len(data["stages"]) == 4
    
    @pytest.mark.asyncio
    async def test_defect_types(self, client):
        """Test defect types endpoint."""
        response = await client.get("/api/v1/defect-types")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "defect_types" in data
        assert len(data["defect_types"]) == 12


class TestSingleInference:
    """Test single inference endpoint."""
    
    @pytest.mark.asyncio
    async def test_infer_normal_module(self, client, sample_thermal_image, sample_metadata):
        """Test inference on normal module (no defects)."""
        payload = {
            "module_id": "mod_test_001",
            "inspection_id": "insp_test_001",
            "image_id": "img_test_001",
            "thermal_data": sample_thermal_image,
            "metadata": sample_metadata
        }
        
        response = await client.post("/api/v1/infer", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "module_id" in data
        assert "defect_type" in data
        assert "severity" in data
        assert "confidence" in data
        assert "processing_time_ms" in data
        
        # Validate response types
        assert isinstance(data["confidence"], float)
        assert 0 <= data["confidence"] <= 1
        assert data["processing_time_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_infer_with_hotspot(self, client, sample_metadata):
        """Test inference with simulated hotspot."""
        # Create image with clear hotspot
        image = np.random.normal(45, 5, (512, 640)).astype(np.float32)
        image[200:250, 300:350] += 30  # Strong hotspot
        
        payload = {
            "module_id": "mod_test_002",
            "inspection_id": "insp_test_001",
            "image_id": "img_test_002",
            "thermal_data": base64.b64encode(image.tobytes()).decode('utf-8'),
            "metadata": sample_metadata
        }
        
        response = await client.post("/api/v1/infer", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should detect defect
        assert data["defect_type"] != "normal" or data["anomaly_score"] > 0.5


class TestBatchInference:
    """Test batch inference endpoint."""
    
    @pytest.mark.asyncio
    async def test_batch_infer(self, client, sample_thermal_image, sample_metadata):
        """Test batch inference."""
        requests = [
            {
                "module_id": f"mod_batch_{i}",
                "inspection_id": "insp_batch_001",
                "image_id": f"img_batch_{i}",
                "thermal_data": sample_thermal_image,
                "metadata": sample_metadata
            }
            for i in range(3)
        ]
        
        payload = {
            "requests": requests,
            "max_batch_size": 8
        }
        
        response = await client.post("/api/v1/infer/batch", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert len(data["results"]) == 3
        assert "total_processing_time_ms" in data
        assert "avg_time_per_image_ms" in data


class TestValidation:
    """Test input validation."""
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client):
        """Test validation for missing required fields."""
        payload = {
            "module_id": "mod_test_001"
            # Missing required fields
        }
        
        response = await client.post("/api/v1/infer", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_invalid_image_size(self, client, sample_metadata):
        """Test with invalid image size."""
        # Create wrong size image
        image = np.random.normal(45, 5, (100, 100)).astype(np.float32)
        
        payload = {
            "module_id": "mod_test_001",
            "inspection_id": "insp_test_001",
            "image_id": "img_test_001",
            "thermal_data": base64.b64encode(image.tobytes()).decode('utf-8'),
            "metadata": sample_metadata
        }
        
        response = await client.post("/api/v1/infer", json=payload)
        
        # Should handle gracefully (resize or error)
        assert response.status_code in [200, 400, 500]


class TestPerformance:
    """Test performance requirements."""
    
    @pytest.mark.asyncio
    async def test_inference_latency(self, client, sample_thermal_image, sample_metadata):
        """Test inference latency is within limits."""
        payload = {
            "module_id": "mod_perf_001",
            "inspection_id": "insp_perf_001",
            "image_id": "img_perf_001",
            "thermal_data": sample_thermal_image,
            "metadata": sample_metadata
        }
        
        response = await client.post("/api/v1/infer", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check latency (should be < 100ms for demo)
        assert data["processing_time_ms"] < 100
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client, sample_thermal_image, sample_metadata):
        """Test handling concurrent requests."""
        payload = {
            "module_id": "mod_concurrent",
            "inspection_id": "insp_concurrent",
            "image_id": "img_concurrent",
            "thermal_data": sample_thermal_image,
            "metadata": sample_metadata
        }
        
        # Send 5 concurrent requests
        tasks = [
            client.post("/api/v1/infer", json=payload)
            for _ in range(5)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200


class TestRedisStreams:
    """Test Redis Streams integration."""
    
    @pytest.mark.asyncio
    async def test_stream_processor_initialization(self):
        """Test stream processor can connect."""
        from redis_streams import MLStreamProcessor
        
        processor = MLStreamProcessor(
            redis_host="localhost",
            group_name="ml-inference-test"
        )
        
        try:
            await processor.connect()
            info = await processor.get_stream_info()
            assert "stream" in info
        except Exception as e:
            # Redis might not be running in test environment
            pytest.skip(f"Redis not available: {e}")
        finally:
            await processor.disconnect()


class TestFeatureExtraction:
    """Test feature extraction modules."""
    
    def test_stage3_features_shape(self):
        """Test Stage 3 feature extraction output shape."""
        from features import extract_stage3_features
        
        # Create sample crop
        crop = np.random.normal(45, 5, (128, 128)).astype(np.float32)
        
        metadata = {
            "neighbor_temps": [45.0] * 4,
            "string_mean": 48.0,
            "array_mean": 47.0,
            "ambient_temp": 35.0,
            "expected_temp": 50.0
        }
        
        result = extract_stage3_features(crop, metadata)
        
        assert result.features.shape == (77,)
        assert len(result.feature_names) == 77
    
    def test_stage4_features_shape(self):
        """Test Stage 4 feature extraction output shape."""
        from features import extract_stage4_features
        
        crop = np.random.normal(45, 5, (128, 128)).astype(np.float32)
        result = extract_stage4_features(crop)
        
        assert result.features.shape == (96,)
        assert len(result.feature_names) == 96


# Integration test markers
@pytest.mark.integration
class TestFullIntegration:
    """Full integration tests requiring all services."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, client, sample_thermal_image, sample_metadata):
        """Test complete end-to-end workflow."""
        # 1. Check service health
        health = await client.get("/health")
        assert health.status_code == 200
        
        # 2. Run inference
        payload = {
            "module_id": "mod_e2e_001",
            "inspection_id": "insp_e2e_001",
            "image_id": "img_e2e_001",
            "thermal_data": sample_thermal_image,
            "metadata": sample_metadata
        }
        
        response = await client.post("/api/v1/infer", json=payload)
        assert response.status_code == 200
        
        result = response.json()
        
        # 3. Validate result structure
        required_fields = [
            "module_id", "defect_type", "severity",
            "confidence", "processing_time_ms"
        ]
        
        for field in required_fields:
            assert field in result
        
        # 4. Check metrics endpoint
        metrics = await client.get("/metrics")
        assert metrics.status_code == 200


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
