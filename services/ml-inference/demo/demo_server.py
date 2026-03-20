#!/usr/bin/env python3
"""
ML Service Demo Server

Runs a demo ML inference server with sample data for frontend integration testing.

Usage:
    python demo_server.py --host 0.0.0.0 --port 8001
"""
import argparse
import base64
import json
import logging
import numpy as np
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ML Inference Demo Service",
    description="Demo ML inference service for thermal solar panel defect detection",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo defect types
DEFECT_TYPES = [
    "hotspot", "cell_anomaly", "delamination", "diode_failure",
    "crack", "soiling", "discoloration", "snail_track",
    "burn_mark", "corrosion", "potential_induced", "broken_cell", "normal"
]

SEVERITY_LEVELS = ["low", "medium", "high", "critical"]


class AnalysisRequest(BaseModel):
    module_id: str
    inspection_id: str
    image_id: str
    thermal_data: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BatchAnalysisRequest(BaseModel):
    requests: List[AnalysisRequest]
    max_batch_size: int = 8


class Recommendation(BaseModel):
    priority: int
    action: str
    description: str
    estimated_power_loss: Optional[str] = None
    safety_risk: Optional[str] = None


class AnalysisResult(BaseModel):
    module_id: str
    inspection_id: str
    image_id: str
    defect_type: str
    severity: str
    severity_score: float
    confidence: float
    temperature_delta: float
    max_temperature: float
    ambient_temperature: float
    affected_cells: List[int]
    recommendations: List[Recommendation]
    anomaly_score: float
    processing_time_ms: float
    model_version: str
    timestamp: str


class BatchAnalysisResult(BaseModel):
    results: List[AnalysisResult]
    count: int
    total_processing_time_ms: float
    avg_time_per_image_ms: float


def generate_demo_result(request: AnalysisRequest) -> AnalysisResult:
    """Generate realistic demo analysis result."""
    import time
    start_time = time.perf_counter()
    
    # Simulate inference latency
    time.sleep(0.025)  # 25ms
    
    # Parse thermal data to estimate defect
    try:
        thermal_bytes = base64.b64decode(request.thermal_data)
        thermal_array = np.frombuffer(thermal_bytes, dtype=np.float32)
        
        # Analyze temperature distribution
        if len(thermal_array) > 100:
            temp_std = np.std(thermal_array)
            temp_max = np.max(thermal_array)
            temp_mean = np.mean(thermal_array)
            temp_delta = temp_max - temp_mean
            
            # Determine defect based on temperature characteristics
            if temp_delta > 25 or temp_std > 15:
                defect_type = "hotspot"
                severity = "critical"
                severity_score = min(0.95, 0.7 + temp_delta / 100)
            elif temp_delta > 15 or temp_std > 10:
                defect_type = "cell_anomaly"
                severity = "high"
                severity_score = min(0.85, 0.5 + temp_delta / 100)
            elif temp_delta > 8 or temp_std > 6:
                defect_type = "delamination"
                severity = "medium"
                severity_score = min(0.65, 0.3 + temp_delta / 100)
            else:
                defect_type = "normal"
                severity = "low"
                severity_score = max(0.05, 0.1 - temp_std / 100)
            
            confidence = min(0.98, 0.75 + temp_std / 50)
            max_temp = float(temp_max)
            ambient_temp = request.metadata.get('ambient_temp', 35.0)
            
        else:
            # Default for small arrays
            defect_type = "normal"
            severity = "low"
            severity_score = 0.1
            confidence = 0.9
            temp_delta = 5.0
            max_temp = 45.0
            ambient_temp = 35.0
            
    except Exception as e:
        logger.warning(f"Error analyzing thermal data: {e}")
        defect_type = "normal"
        severity = "low"
        severity_score = 0.1
        confidence = 0.9
        temp_delta = 5.0
        max_temp = 45.0
        ambient_temp = 35.0
    
    # Generate recommendations
    recommendations = []
    if severity == "critical":
        recommendations = [
            Recommendation(
                priority=1,
                action="IMMEDIATE_REPLACEMENT",
                description=f"Module shows critical {defect_type} with {temp_delta:.1f}°C temperature delta",
                estimated_power_loss="15-20%",
                safety_risk="Fire hazard - thermal runaway possible"
            ),
            Recommendation(
                priority=2,
                action="INSPECT_ADJACENT_MODULES",
                description="Check modules in same substring for cascading issues"
            )
        ]
    elif severity == "high":
        recommendations = [
            Recommendation(
                priority=1,
                action="SCHEDULE_REPLACEMENT",
                description=f"Module shows significant {defect_type}, schedule replacement within 7 days",
                estimated_power_loss="10-15%",
                safety_risk="Moderate - monitor closely"
            )
        ]
    elif severity == "medium":
        recommendations = [
            Recommendation(
                priority=1,
                action="SCHEDULE_INSPECTION",
                description=f"Module shows moderate {defect_type}, schedule inspection within 30 days",
                estimated_power_loss="5-10%",
                safety_risk="Low"
            )
        ]
    else:
        recommendations = [
            Recommendation(
                priority=0,
                action="NO_ACTION",
                description="Module operating normally, no defects detected"
            )
        ]
    
    # Generate affected cells (for demo)
    if defect_type != "normal":
        affected_cells = np.random.choice(range(60), size=np.random.randint(2, 6), replace=False).tolist()
    else:
        affected_cells = []
    
    processing_time = (time.perf_counter() - start_time) * 1000
    
    return AnalysisResult(
        module_id=request.module_id,
        inspection_id=request.inspection_id,
        image_id=request.image_id,
        defect_type=defect_type,
        severity=severity,
        severity_score=round(severity_score, 3),
        confidence=round(confidence, 3),
        temperature_delta=round(temp_delta, 1),
        max_temperature=round(max_temp, 1),
        ambient_temperature=ambient_temp,
        affected_cells=affected_cells,
        recommendations=recommendations,
        anomaly_score=round(1.0 - confidence + np.random.uniform(0, 0.1), 3),
        processing_time_ms=round(processing_time, 1),
        model_version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ml-inference-demo",
        "version": "1.0.0",
        "models_loaded": True,
        "stages": 4
    }


@app.get("/metrics")
async def get_metrics():
    """Service metrics."""
    return {
        "model_version": "1.0.0",
        "device": "demo",
        "inference_timeout_ms": 35,
        "stages": {
            "stage1": {"name": "Hotspot Detector", "model": "YOLOv8n-seg", "latency_ms": 2.5},
            "stage2": {"name": "Cell Analyzer", "model": "YOLOv8m", "latency_ms": 8.0},
            "stage3": {"name": "Module Classifier", "model": "YOLOv8m", "latency_ms": 12.0},
            "stage4": {"name": "Severity Scorer", "model": "XGBoost", "latency_ms": 0.3}
        },
        "performance": {
            "total_latency_ms": 22.8,
            "throughput_per_sec": 44
        }
    }


@app.get("/api/v1/ml/stages")
async def get_stages():
    """Get pipeline stages information."""
    return {
        "stages": [
            {
                "id": 1,
                "name": "Module Segmentation",
                "description": "Detect and segment solar modules from thermal imagery",
                "architecture": "YOLOv8n-seg",
                "input": {"shape": [640, 512, 1], "type": "thermal_image"},
                "output": {"type": "segmentation_masks"},
                "latency_ms": 8.0,
                "model_size_mb": 8.5,
                "accuracy": 0.962
            },
            {
                "id": 2,
                "name": "Defect Detection",
                "description": "Detect and classify 12 types of defects",
                "architecture": "YOLOv8m",
                "input": {"shape": [128, 128, 1], "type": "module_crop"},
                "output": {"classes": 12, "type": "defect_bboxes"},
                "latency_ms": 12.0,
                "model_size_mb": 52.0,
                "accuracy": 0.931
            },
            {
                "id": 3,
                "name": "Severity Scoring",
                "description": "Classify defect severity into 3 levels",
                "architecture": "XGBoost",
                "input": {"dim": 77, "type": "feature_vector"},
                "output": {"classes": 3, "type": "severity_probs"},
                "latency_ms": 0.3,
                "model_size_mb": 25.0,
                "accuracy": 0.952
            },
            {
                "id": 4,
                "name": "Anomaly Detection",
                "description": "Detect novel defects not in training set",
                "architecture": "ConvAE + IsolationForest",
                "input": {"dim": 96, "type": "feature_vector"},
                "output": {"type": "anomaly_score"},
                "latency_ms": 1.8,
                "model_size_mb": 7.3,
                "accuracy": 0.884
            }
        ],
        "total_latency_ms": 22.1,
        "total_model_size_mb": 92.8
    }


@app.get("/api/v1/ml/defect-types")
async def get_defect_types():
    """Get supported defect types."""
    defect_info = {
        "hotspot": {"id": 0, "name": "hotspot", "description": "Localized overheating", "severity_range": "medium-critical", "frequency": "28%"},
        "cell_anomaly": {"id": 1, "name": "cell_anomaly", "description": "Cell-level irregularity", "severity_range": "low-high", "frequency": "25%"},
        "delamination": {"id": 2, "name": "delamination", "description": "Layer separation", "severity_range": "medium-high", "frequency": "15%"},
        "diode_failure": {"id": 3, "name": "diode_failure", "description": "Bypass diode malfunction", "severity_range": "high-critical", "frequency": "10%"},
        "crack": {"id": 4, "name": "crack", "description": "Physical fracture", "severity_range": "medium-high", "frequency": "8%"},
        "soiling": {"id": 5, "name": "soiling", "description": "Dirt accumulation", "severity_range": "low-medium", "frequency": "4%"},
        "discoloration": {"id": 6, "name": "discoloration", "description": "UV degradation", "severity_range": "low", "frequency": "3%"},
        "snail_track": {"id": 7, "name": "snail_track", "description": "Micro-crack pattern", "severity_range": "low-medium", "frequency": "5%"},
        "burn_mark": {"id": 8, "name": "burn_mark", "description": "Thermal damage", "severity_range": "high-critical", "frequency": "4%"},
        "corrosion": {"id": 9, "name": "corrosion", "description": "Contact oxidation", "severity_range": "low-medium", "frequency": "4%"},
        "potential_induced": {"id": 10, "name": "potential_induced", "description": "PID effect", "severity_range": "high-critical", "frequency": "3%"},
        "broken_cell": {"id": 11, "name": "broken_cell", "description": "Cell damage", "severity_range": "high-critical", "frequency": "8%"},
        "normal": {"id": 12, "name": "normal", "description": "No defect", "severity_range": "none", "frequency": "Variable"}
    }
    
    return {
        "defect_types": list(defect_info.values())
    }


@app.get("/api/v1/ml/severity-levels")
async def get_severity_levels():
    """Get severity level definitions."""
    return {
        "severity_levels": [
            {
                "level": "low",
                "score_range": [0.0, 0.25],
                "action": "Monitor",
                "timeline": "No immediate action",
                "color": "#22c55e"
            },
            {
                "level": "medium",
                "score_range": [0.25, 0.50],
                "action": "Schedule Maintenance",
                "timeline": "Within 30 days",
                "color": "#eab308"
            },
            {
                "level": "high",
                "score_range": [0.50, 0.75],
                "action": "Priority Maintenance",
                "timeline": "Within 7 days",
                "color": "#f97316"
            },
            {
                "level": "critical",
                "score_range": [0.75, 1.0],
                "action": "Immediate Replacement",
                "timeline": "Within 24-48 hours",
                "color": "#ef4444"
            }
        ]
    }


@app.post("/api/v1/ml/infer", response_model=AnalysisResult)
async def infer(request: AnalysisRequest):
    """Run ML inference on a single thermal image."""
    logger.info(f"Analyzing module {request.module_id}")
    result = generate_demo_result(request)
    logger.info(f"Result: {result.defect_type} ({result.severity}, {result.confidence:.1%})")
    return result


@app.post("/api/v1/ml/infer/batch", response_model=BatchAnalysisResult)
async def infer_batch(request: BatchAnalysisRequest):
    """Run batch inference on multiple thermal images."""
    import time
    start_time = time.perf_counter()
    
    results = []
    for req in request.requests:
        result = generate_demo_result(req)
        results.append(result)
    
    total_time = (time.perf_counter() - start_time) * 1000
    
    return BatchAnalysisResult(
        results=results,
        count=len(results),
        total_processing_time_ms=round(total_time, 1),
        avg_time_per_image_ms=round(total_time / len(results), 1) if results else 0
    )


def main():
    parser = argparse.ArgumentParser(description='ML Demo Server')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8001, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    args = parser.parse_args()
    
    print("=" * 70)
    print("ML Inference Demo Server")
    print("=" * 70)
    print()
    print(f"Starting server on http://{args.host}:{args.port}")
    print()
    print("Endpoints:")
    print("  GET  /health              - Health check")
    print("  GET  /metrics             - Service metrics")
    print("  GET  /api/v1/ml/stages    - Pipeline stages")
    print("  GET  /api/v1/ml/defect-types  - Defect types")
    print("  GET  /api/v1/ml/severity-levels - Severity levels")
    print("  POST /api/v1/ml/infer     - Single inference")
    print("  POST /api/v1/ml/infer/batch - Batch inference")
    print()
    print("Frontend Integration:")
    print(f"  Set VITE_API_URL=http://localhost:{args.port}/api/v1")
    print()
    
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == '__main__':
    main()
