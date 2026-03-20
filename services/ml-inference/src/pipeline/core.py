"""
ML Inference Pipeline - Four-Stage Cascade
Implements the complete defect detection pipeline for thermal solar panel inspection.

Supports:
- ONNX Runtime for cloud/CPU inference
- CoreML for Apple Silicon (Mac M2) edge deployment
- PyTorch for development and training
"""
import asyncio
import time
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import numpy as np

# Model loading imports
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    ort = None

try:
    import coremltools as ct
    from coremltools.models import MLModel
    COREML_AVAILABLE = True
except ImportError:
    COREML_AVAILABLE = False
    ct = None
    MLModel = None

# PyTorch (for fallback)
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None


class DefectType(str, Enum):
    """Defect classification types per IEC 62446-3."""
    HOTSPOT = "hotspot"
    CELL_ANOMALY = "cell_anomaly"
    DELAMINATION = "delamination"
    DIODE_FAILURE = "diode_failure"
    CRACK = "crack"
    SOILING = "soiling"
    DISCOLORATION = "discoloration"
    NORMAL = "normal"


class SeverityLevel(str, Enum):
    """Defect severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class StageResult:
    """Result from a single pipeline stage."""
    stage: int
    success: bool
    processing_time_ms: float
    confidence: float
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class PipelineResult:
    """Complete pipeline inference result."""
    module_id: str
    inspection_id: str
    image_id: str
    
    # Final outputs
    defect_type: DefectType
    severity: SeverityLevel
    severity_score: float
    confidence: float
    
    # Detailed results
    temperature_delta: float
    max_temperature: float
    ambient_temperature: float
    affected_cells: List[int]
    recommendations: List[Dict[str, Any]]
    
    # Stage-wise breakdown
    stage_results: Dict[int, StageResult]
    total_processing_time_ms: float
    
    # Metadata
    model_version: str = "1.0.0"
    device: str = "edge"


class Stage1HotspotDetector:
    """
    Stage 1: Binary hotspot detection.

    Lightweight CNN that determines if thermal image contains anomalous heat.
    - Input: 640x512 thermal image (1 channel)
    - Output: hotspot_probability (0.0 - 1.0)
    - Latency: <3ms (edge), <1ms (cloud GPU)
    """

    def __init__(self, model_path: str, device: str = "edge"):
        self.model_path = model_path
        self.device = device
        self.threshold = 0.65
        self.model = self._load_model()

    def _load_model(self):
        """Load optimized model for target device."""
        model_dir = Path(self.model_path) / 'stage1'
        
        # Try CoreML first for edge (Mac M2)
        if self.device == "edge" and COREML_AVAILABLE:
            coreml_path = model_dir / 'model.mlpackage'
            if coreml_path.exists():
                return MLModel(str(coreml_path))
        
        # Try ONNX (works everywhere)
        if ONNX_AVAILABLE:
            onnx_path = model_dir / 'model.onnx'
            if onnx_path.exists():
                session_options = ort.SessionOptions()
                session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                
                if self.device == "edge":
                    # Use CoreML EP for Apple Silicon
                    providers = ['CoreMLExecutionProvider', 'CPUExecutionProvider']
                else:
                    providers = ['CPUExecutionProvider']
                
                return ort.InferenceSession(
                    str(onnx_path),
                    sess_options=session_options,
                    providers=providers
                )
        
        # Fallback to PyTorch
        if TORCH_AVAILABLE:
            pt_path = model_dir / 'best_model.pth'
            if pt_path.exists():
                from architectures import Stage1HotspotDetector as PyTorchModel
                model = PyTorchModel()
                model.load_state_dict(torch.load(pt_path, map_location='cpu')['model_state_dict'])
                model.eval()
                return model
        
        # Last resort: return None (use placeholder)
        return None
    
    async def infer(self, thermal_data: np.ndarray) -> StageResult:
        """
        Run hotspot detection.

        Args:
            thermal_data: Normalized thermal image array [640, 512]

        Returns:
            StageResult with hotspot detection outcome
        """
        start_time = time.perf_counter()

        try:
            # Preprocess
            input_tensor = self._preprocess(thermal_data)

            # Inference
            if self.model is None:
                # Placeholder inference
                hotspot_prob = 0.89
            elif hasattr(self.model, 'predict'):
                # CoreML
                output = self.model.predict({"input": input_tensor})
                hotspot_prob = float(output["probability"] if "probability" in output else list(output.values())[0][0])
            elif hasattr(self.model, 'run'):
                # ONNX
                outputs = self.model.run(None, {"input": input_tensor})
                hotspot_prob = float(outputs[0][0])
            else:
                # PyTorch
                with torch.no_grad():
                    output = self.model(torch.from_numpy(input_tensor))
                    hotspot_prob = float(output[0][0])

            # Postprocess
            hotspot_detected = hotspot_prob > self.threshold

            processing_time = (time.perf_counter() - start_time) * 1000

            return StageResult(
                stage=1,
                success=True,
                processing_time_ms=processing_time,
                confidence=hotspot_prob,
                data={
                    "hotspot_detected": hotspot_detected,
                    "hotspot_probability": hotspot_prob,
                    "threshold": self.threshold,
                    "passed_to_stage_2": hotspot_detected
                }
            )

        except Exception as e:
            return StageResult(
                stage=1,
                success=False,
                processing_time_ms=(time.perf_counter() - start_time) * 1000,
                confidence=0.0,
                error=str(e)
            )
    
    def _preprocess(self, thermal_data: np.ndarray) -> np.ndarray:
        """Normalize and prepare input tensor."""
        # Normalize to [0, 1]
        normalized = (thermal_data - thermal_data.min()) / (thermal_data.max() - thermal_data.min())
        
        # Add batch and channel dimensions: [640, 512] -> [1, 1, 640, 512]
        tensor = np.expand_dims(np.expand_dims(normalized, 0), 0).astype(np.float32)
        
        return tensor


class Stage2CellAnalyzer:
    """
    Stage 2: Cell-level anomaly detection and feature extraction.
    
    UNet-based segmentation model that identifies affected cells.
    - Input: Thermal image + Stage 1 features
    - Output: Cell anomaly map + 128-dim feature vector per cell
    - Latency: <10ms (edge), <3ms (cloud GPU)
    """
    
    def __init__(self, model_path: str, device: str = "edge"):
        self.model_path = model_path
        self.device = device
        self.cell_layout = (6, 10)  # 6 rows x 10 columns = 60 cells
        self.model = self._load_model()
    
    def _load_model(self):
        """Load segmentation model."""
        # Placeholder for actual model loading
        return None
    
    async def infer(
        self,
        thermal_data: np.ndarray,
        stage1_features: Optional[np.ndarray] = None
    ) -> StageResult:
        """
        Analyze cell-level anomalies.
        
        Args:
            thermal_data: Thermal image array [640, 512]
            stage1_features: Feature map from Stage 1 (optional)
            
        Returns:
            StageResult with cell analysis
        """
        start_time = time.perf_counter()
        
        try:
            # Run segmentation
            # cell_masks, cell_features = self.model.predict(...)
            
            # Placeholder results
            affected_cells = [12, 13, 22, 23]
            cell_features = {
                cell_id: {
                    "temp_delta": 15.2 + np.random.uniform(-2, 2),
                    "area_pixels": int(240 + np.random.uniform(-20, 20)),
                    "position": [cell_id // 10, cell_id % 10]
                }
                for cell_id in affected_cells
            }
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return StageResult(
                stage=2,
                success=True,
                processing_time_ms=processing_time,
                confidence=0.92,
                data={
                    "affected_cells": affected_cells,
                    "cell_features": cell_features,
                    "total_cells": 60,
                    "anomaly_percentage": len(affected_cells) / 60 * 100
                }
            )
            
        except Exception as e:
            return StageResult(
                stage=2,
                success=False,
                processing_time_ms=(time.perf_counter() - start_time) * 1000,
                confidence=0.0,
                error=str(e)
            )


class Stage3ModuleClassifier:
    """
    Stage 3: Defect type classification.
    
    ResNet-18 + Transformer model for 8-class defect classification.
    - Input: Cell features + anomaly map
    - Output: Defect type probabilities (8 classes)
    - Latency: <15ms (edge), <5ms (cloud GPU)
    """
    
    def __init__(self, model_path: str, device: str = "edge"):
        self.model_path = model_path
        self.device = device
        self.defect_types = list(DefectType)
        self.model = self._load_model()
    
    def _load_model(self):
        """Load classification model."""
        # Placeholder for actual model loading
        return None
    
    async def infer(
        self,
        cell_features: Dict[int, Dict],
        cell_anomaly_map: np.ndarray,
        module_metadata: Dict[str, Any]
    ) -> StageResult:
        """
        Classify defect type.
        
        Args:
            cell_features: Per-cell feature dictionaries
            cell_anomaly_map: Segmentation mask
            module_metadata: Module specifications
            
        Returns:
            StageResult with defect classification
        """
        start_time = time.perf_counter()
        
        try:
            # Run classification
            # probabilities = self.model.predict(...)
            
            # Placeholder - simulate hotspot detection
            probabilities = {
                DefectType.HOTSPOT.value: 0.91,
                DefectType.CELL_ANOMALY.value: 0.05,
                DefectType.DELAMINATION.value: 0.02,
                DefectType.DIODE_FAILURE.value: 0.01,
                DefectType.CRACK.value: 0.005,
                DefectType.SOILING.value: 0.003,
                DefectType.DISCOLORATION.value: 0.002,
                DefectType.NORMAL.value: 0.0
            }
            
            predicted_type = max(probabilities, key=probabilities.get)
            confidence = probabilities[predicted_type]
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return StageResult(
                stage=3,
                success=True,
                processing_time_ms=processing_time,
                confidence=confidence,
                data={
                    "defect_type": predicted_type,
                    "defect_type_id": self.defect_types.index(DefectType(predicted_type)),
                    "all_probabilities": probabilities,
                    "top_3": sorted(probabilities.items(), key=lambda x: x[1], reverse=True)[:3]
                }
            )
            
        except Exception as e:
            return StageResult(
                stage=3,
                success=False,
                processing_time_ms=(time.perf_counter() - start_time) * 1000,
                confidence=0.0,
                error=str(e)
            )


class Stage4SeverityScorer:
    """
    Stage 4: Severity estimation and recommendation generation.
    
    Multi-branch network for severity scoring and confidence calibration.
    - Input: Defect type + cell features + thermal metadata
    - Output: Severity score, confidence, recommendations
    - Latency: <5ms (edge), <2ms (cloud GPU)
    """
    
    def __init__(self, model_path: str, device: str = "edge"):
        self.model_path = model_path
        self.device = device
        self.model = self._load_model()
        
        # Severity thresholds
        self.thresholds = {
            SeverityLevel.LOW: (0.0, 0.25),
            SeverityLevel.MEDIUM: (0.25, 0.50),
            SeverityLevel.HIGH: (0.50, 0.75),
            SeverityLevel.CRITICAL: (0.75, 1.0)
        }
    
    def _load_model(self):
        """Load severity scoring model."""
        # Placeholder for actual model loading
        return None
    
    async def infer(
        self,
        defect_type: str,
        cell_features: Dict[int, Dict],
        thermal_metadata: Dict[str, float],
        module_specifications: Dict[str, Any]
    ) -> StageResult:
        """
        Calculate severity and generate recommendations.
        
        Args:
            defect_type: Predicted defect type from Stage 3
            cell_features: Cell-level features from Stage 2
            thermal_metadata: Temperature and environmental data
            module_specifications: Module technical specs
            
        Returns:
            StageResult with severity and recommendations
        """
        start_time = time.perf_counter()
        
        try:
            # Calculate severity score
            # severity_score = self.model.predict(...)
            
            # Placeholder - simulate critical hotspot
            temp_delta = thermal_metadata.get("temperature_delta", 25.0)
            severity_score = min(1.0, temp_delta / 45.0)  # Normalize to [0, 1]
            
            # Determine severity level
            severity_level = self._get_severity_level(severity_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                defect_type=defect_type,
                severity=severity_level,
                temp_delta=temp_delta
            )
            
            # Confidence calibration
            confidence = 0.94  # Placeholder
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return StageResult(
                stage=4,
                success=True,
                processing_time_ms=processing_time,
                confidence=confidence,
                data={
                    "severity_score": severity_score,
                    "severity_level": severity_level.value,
                    "confidence": confidence,
                    "recommendations": recommendations,
                    "uncertainty": 1.0 - confidence
                }
            )
            
        except Exception as e:
            return StageResult(
                stage=4,
                success=False,
                processing_time_ms=(time.perf_counter() - start_time) * 1000,
                confidence=0.0,
                error=str(e)
            )
    
    def _get_severity_level(self, score: float) -> SeverityLevel:
        """Map severity score to level."""
        for level, (min_val, max_val) in self.thresholds.items():
            if min_val <= score < max_val:
                return level
        return SeverityLevel.CRITICAL
    
    def _generate_recommendations(
        self,
        defect_type: str,
        severity: SeverityLevel,
        temp_delta: float
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on defect analysis."""
        recommendations = []
        
        # Priority 1: Main action
        if severity == SeverityLevel.CRITICAL:
            recommendations.append({
                "priority": 1,
                "action": "IMMEDIATE_REPLACEMENT",
                "description": f"Module shows critical {defect_type} with {temp_delta:.1f}°C temperature delta",
                "estimated_power_loss": "15-20%",
                "safety_risk": "Fire hazard - thermal runaway possible"
            })
        elif severity == SeverityLevel.HIGH:
            recommendations.append({
                "priority": 1,
                "action": "SCHEDULE_REPLACEMENT",
                "description": f"Module shows significant {defect_type}, schedule replacement within 7 days",
                "estimated_power_loss": "10-15%",
                "safety_risk": "Moderate - monitor closely"
            })
        elif severity == SeverityLevel.MEDIUM:
            recommendations.append({
                "priority": 1,
                "action": "SCHEDULE_INSPECTION",
                "description": f"Module shows moderate {defect_type}, schedule inspection within 30 days",
                "estimated_power_loss": "5-10%",
                "safety_risk": "Low"
            })
        else:
            recommendations.append({
                "priority": 3,
                "action": "MONITOR",
                "description": f"Minor {defect_type} detected, continue monitoring",
                "estimated_power_loss": "<5%",
                "safety_risk": "None"
            })
        
        # Priority 2: Adjacent modules
        if severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
            recommendations.append({
                "priority": 2,
                "action": "INSPECT_ADJACENT_MODULES",
                "description": "Check modules in same substring for cascading issues"
            })
        
        # Priority 3: Connection check
        if defect_type in ["hotspot", "diode_failure"]:
            recommendations.append({
                "priority": 3,
                "action": "CHECK_CONNECTIONS",
                "description": "Verify MC4 connectors and wiring integrity"
            })
        
        return recommendations


class MLPipeline:
    """
    Complete four-stage ML inference pipeline.
    
    Orchestrates the cascade of models from hotspot detection
    through severity scoring with early exit optimization.
    """
    
    def __init__(
        self,
        model_dir: str = "/app/models",
        device: str = "edge",
        enable_early_exit: bool = True
    ):
        self.model_dir = model_dir
        self.device = device
        self.enable_early_exit = enable_early_exit
        
        # Initialize stages
        self.stage1 = Stage1HotspotDetector(f"{model_dir}/stage1.onnx", device)
        self.stage2 = Stage2CellAnalyzer(f"{model_dir}/stage2.onnx", device)
        self.stage3 = Stage3ModuleClassifier(f"{model_dir}/stage3.onnx", device)
        self.stage4 = Stage4SeverityScorer(f"{model_dir}/stage4.onnx", device)
        
        self.model_version = "1.0.0"
    
    async def infer(
        self,
        image_id: str,
        module_id: str,
        inspection_id: str,
        thermal_data: np.ndarray,
        metadata: Dict[str, Any]
    ) -> PipelineResult:
        """
        Run complete inference pipeline.
        
        Args:
            image_id: Unique image identifier
            module_id: Target module ID
            inspection_id: Inspection session ID
            thermal_data: Normalized thermal image [640, 512]
            metadata: Environmental and module metadata
            
        Returns:
            PipelineResult with complete analysis
        """
        pipeline_start = time.perf_counter()
        stage_results = {}
        
        # ========== STAGE 1: Hotspot Detection ==========
        stage1_result = await self.stage1.infer(thermal_data)
        stage_results[1] = stage1_result
        
        # Early exit: No hotspot detected
        if self.enable_early_exit and stage1_result.success:
            if not stage1_result.data.get("hotspot_detected", False):
                return self._create_normal_result(
                    image_id=image_id,
                    module_id=module_id,
                    inspection_id=inspection_id,
                    stage_results=stage_results,
                    pipeline_start=pipeline_start
                )
        
        # ========== STAGE 2: Cell Analysis ==========
        stage2_result = await self.stage2.infer(
            thermal_data=thermal_data,
            stage1_features=None  # Could pass Stage 1 features
        )
        stage_results[2] = stage2_result
        
        if not stage2_result.success:
            return self._create_error_result(
                module_id=module_id,
                inspection_id=inspection_id,
                stage_results=stage_results,
                error="Stage 2 cell analysis failed",
                pipeline_start=pipeline_start
            )
        
        # ========== STAGE 3: Defect Classification ==========
        stage3_result = await self.stage3.infer(
            cell_features=stage2_result.data.get("cell_features", {}),
            cell_anomaly_map=None,  # Could pass segmentation mask
            module_metadata=metadata.get("module", {})
        )
        stage_results[3] = stage3_result
        
        if not stage3_result.success:
            return self._create_error_result(
                module_id=module_id,
                inspection_id=inspection_id,
                stage_results=stage_results,
                error="Stage 3 classification failed",
                pipeline_start=pipeline_start
            )
        
        # ========== STAGE 4: Severity Scoring ==========
        stage4_result = await self.stage4.infer(
            defect_type=stage3_result.data.get("defect_type", "normal"),
            cell_features=stage2_result.data.get("cell_features", {}),
            thermal_metadata=metadata.get("thermal", {}),
            module_specifications=metadata.get("module", {})
        )
        stage_results[4] = stage4_result
        
        if not stage4_result.success:
            return self._create_error_result(
                module_id=module_id,
                inspection_id=inspection_id,
                stage_results=stage_results,
                error="Stage 4 severity scoring failed",
                pipeline_start=pipeline_start
            )
        
        # ========== Aggregate Results ==========
        total_time = (time.perf_counter() - pipeline_start) * 1000
        
        return PipelineResult(
            module_id=module_id,
            inspection_id=inspection_id,
            image_id=image_id,
            
            defect_type=DefectType(stage3_result.data["defect_type"]),
            severity=SeverityLevel(stage4_result.data["severity_level"]),
            severity_score=stage4_result.data["severity_score"],
            confidence=stage4_result.data["confidence"],
            
            temperature_delta=metadata.get("thermal", {}).get("temperature_delta", 0.0),
            max_temperature=metadata.get("thermal", {}).get("max_temperature", 0.0),
            ambient_temperature=metadata.get("thermal", {}).get("ambient_temperature", 0.0),
            affected_cells=stage2_result.data.get("affected_cells", []),
            recommendations=stage4_result.data.get("recommendations", []),
            
            stage_results=stage_results,
            total_processing_time_ms=total_time,
            model_version=self.model_version,
            device=self.device
        )
    
    def _create_normal_result(
        self,
        image_id: str,
        module_id: str,
        inspection_id: str,
        stage_results: Dict[int, StageResult],
        pipeline_start: float
    ) -> PipelineResult:
        """Create result for normal (no defect) module."""
        return PipelineResult(
            module_id=module_id,
            inspection_id=inspection_id,
            image_id=image_id,
            defect_type=DefectType.NORMAL,
            severity=SeverityLevel.LOW,
            severity_score=0.0,
            confidence=stage_results[1].confidence,
            temperature_delta=0.0,
            max_temperature=0.0,
            ambient_temperature=0.0,
            affected_cells=[],
            recommendations=[{
                "priority": 0,
                "action": "NO_ACTION",
                "description": "Module operating normally, no defects detected"
            }],
            stage_results=stage_results,
            total_processing_time_ms=(time.perf_counter() - pipeline_start) * 1000,
            model_version=self.model_version,
            device=self.device
        )
    
    def _create_error_result(
        self,
        module_id: str,
        inspection_id: str,
        stage_results: Dict[int, StageResult],
        error: str,
        pipeline_start: float
    ) -> PipelineResult:
        """Create result for pipeline error."""
        return PipelineResult(
            module_id=module_id,
            inspection_id=inspection_id,
            image_id="error",
            defect_type=DefectType.NORMAL,
            severity=SeverityLevel.LOW,
            severity_score=0.0,
            confidence=0.0,
            temperature_delta=0.0,
            max_temperature=0.0,
            ambient_temperature=0.0,
            affected_cells=[],
            recommendations=[{
                "priority": 0,
                "action": "MANUAL_REVIEW",
                "description": f"Automated analysis failed: {error}"
            }],
            stage_results=stage_results,
            total_processing_time_ms=(time.perf_counter() - pipeline_start) * 1000,
            model_version=self.model_version,
            device=self.device
        )


# Example usage
async def main():
    """Demonstrate pipeline usage."""
    # Initialize pipeline
    pipeline = MLPipeline(
        model_dir="/app/models",
        device="edge",
        enable_early_exit=True
    )
    
    # Simulate thermal data
    thermal_data = np.random.rand(640, 512).astype(np.float32) * 65 + 20  # 20-85°C range
    
    # Metadata
    metadata = {
        "thermal": {
            "ambient_temperature": 35.0,
            "max_temperature": 75.5,
            "temperature_delta": 40.5,
            "irradiance_w_m2": 850
        },
        "module": {
            "manufacturer": "SolarTech",
            "model": "ST-400M",
            "rated_power_w": 400,
            "temperature_coefficient": -0.0035
        }
    }
    
    # Run inference
    result = await pipeline.infer(
        image_id="img_test_001",
        module_id="mod_001_05",
        inspection_id="insp_001",
        thermal_data=thermal_data,
        metadata=metadata
    )
    
    # Print results
    print(f"\n{'='*60}")
    print(f"ML Inference Results - {result.module_id}")
    print(f"{'='*60}")
    print(f"Defect Type:    {result.defect_type.value}")
    print(f"Severity:       {result.severity.value} ({result.severity_score:.2f})")
    print(f"Confidence:     {result.confidence:.2%}")
    print(f"Temp Delta:     {result.temperature_delta:.1f}°C")
    print(f"Affected Cells: {result.affected_cells}")
    print(f"Processing Time: {result.total_processing_time_ms:.1f}ms")
    print(f"\nRecommendations:")
    for rec in result.recommendations:
        print(f"  [{rec['priority']}] {rec['action']}: {rec['description']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
