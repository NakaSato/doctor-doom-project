# ML Inference Service - Complete Architecture

## Overview

The ML Inference Service implements a **four-stage cascade pipeline** for thermal solar panel defect detection, optimized for edge deployment on Mac M2 with CoreML acceleration.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Stage 1    │ →  │  Stage 2    │ →  │  Stage 3    │ →  │  Stage 4    │
│  Hotspot    │    │  Cell       │    │  Module     │    │  Severity   │
│  Detector   │    │  Analyzer   │    │  Classifier │    │  Scorer     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     2.5ms              8ms               12ms              5ms
     ✓/✗                Type             Defect            Confidence
                        Identified       Classified        + Temperature
```

**Total Pipeline Latency:** <35ms per module (edge), <15ms (cloud with GPU)

---

## Stage 1: Hotspot Detector

### Purpose
Binary classification to identify if a thermal image contains any anomalous heat signatures.

### Architecture
```
Input: 640x512 thermal image (1 channel)
       ↓
[Conv2D 32, 3x3, stride=2] → BatchNorm → ReLU
       ↓
[Conv2D 64, 3x3, stride=2] → BatchNorm → ReLU
       ↓
[Conv2D 128, 3x3, stride=2] → BatchNorm → ReLU
       ↓
[Global Average Pooling]
       ↓
[Dense 128] → ReLU → Dropout(0.3)
       ↓
[Dense 1] → Sigmoid
       ↓
Output: hotspot_probability (0.0 - 1.0)
```

### Parameters
- **Model Size:** 2.1 MB
- **FLOPs:** 45M
- **Threshold:** 0.65 (configurable)
- **Format:** ONNX → CoreML (edge) / TensorRT (cloud)

### Input/Output

**Input:**
```json
{
  "thermal_data": "base64_encoded_radiometric_jpeg",
  "image_shape": [640, 512],
  "temperature_range": {"min": 20.5, "max": 85.2}
}
```

**Output:**
```json
{
  "stage": 1,
  "hotspot_detected": true,
  "confidence": 0.89,
  "processing_time_ms": 2.5,
  "passed_to_stage_2": true
}
```

### Training Configuration

```python
# Dataset
- Positive samples: 15,000 images with hotspots
- Negative samples: 25,000 images without hotspots
- Augmentation: rotation, flip, temperature shift, noise

# Hyperparameters
optimizer: AdamW
learning_rate: 1e-3
batch_size: 64
epochs: 50
loss: BinaryCrossEntropy(weighted)
metrics: [accuracy, precision, recall, f1]

# Class weights (handle imbalance)
pos_weight: 1.67  # 25000/15000
```

### Performance Metrics

| Metric | Value |
|--------|-------|
| Accuracy | 97.2% |
| Precision | 95.8% |
| Recall | 98.1% |
| F1 Score | 96.9% |
| False Positive Rate | 2.8% |

---

## Stage 2: Cell Analyzer

### Purpose
Identify which specific cells within the module are affected and extract cell-level features.

### Architecture
```
Input: 640x512 thermal image + Stage 1 feature map
       ↓
[UNet Encoder]
├─ Conv2D 64, 3x3 → BatchNorm → ReLU
├─ Conv2D 128, 3x3 → BatchNorm → ReLU
├─ Conv2D 256, 3x3 → BatchNorm → ReLU
└─ Conv2D 512, 3x3 → BatchNorm → ReLU
       ↓
[Bottleneck]
       ↓
[UNet Decoder with Skip Connections]
       ↓
[Cell Segmentation Head]        [Feature Extraction Head]
       ↓                                ↓
60 cell masks (6x10 grid)        128-dim feature vector
       ↓                                ↓
Output: cell_anomaly_map          Output: cell_features
```

### Parameters
- **Model Size:** 18.5 MB
- **FLOPs:** 380M
- **Grid:** 6x10 cells (60 total per module)
- **Format:** ONNX → CoreML

### Input/Output

**Input:**
```json
{
  "thermal_data": "base64_encoded_image",
  "stage1_features": "base64_encoded_features",
  "cell_layout": {"rows": 6, "cols": 10}
}
```

**Output:**
```json
{
  "stage": 2,
  "affected_cells": [12, 13, 22, 23],
  "cell_anomaly_map": "base64_encoded_mask",
  "cell_features": {
    "12": {"temp_delta": 15.2, "area_pixels": 245, "position": [2, 2]},
    "13": {"temp_delta": 14.8, "area_pixels": 238, "position": [2, 3]},
    "22": {"temp_delta": 8.5, "area_pixels": 156, "position": [3, 2]},
    "23": {"temp_delta": 9.1, "area_pixels": 162, "position": [3, 3]}
  },
  "processing_time_ms": 8.0
}
```

### Training Configuration

```python
# Dataset
- Segmentation masks: 8,000 annotated images
- Cell boundaries: manually labeled + synthetic

# Loss Functions
segmentation_loss: DiceLoss + BCELoss
feature_loss: ContrastiveLoss

# Hyperparameters
optimizer: AdamW
learning_rate: 5e-4
batch_size: 16
epochs: 80
```

### Performance Metrics

| Metric | Value |
|--------|-------|
| Cell Detection Accuracy | 94.5% |
| IoU (Segmentation) | 0.87 |
| Cell Feature MAE | 1.2°C |

---

## Stage 3: Module Classifier

### Purpose
Classify the specific defect type based on cell patterns and thermal signatures.

### Defect Types

| ID | Defect Type | Description | Thermal Pattern |
|----|-------------|-------------|-----------------|
| 0 | `hotspot` | Localized overheating | Small circular high-temp region |
| 1 | `cell_anomaly` | Cell-level irregularity | Single/multiple cells different |
| 2 | `delamination` | Layer separation | Diffuse irregular pattern |
| 3 | `diode_failure` | Bypass diode malfunction | Entire substring affected |
| 4 | `crack` | Physical fracture | Linear thermal discontinuity |
| 5 | `soiling` | Dirt/debris accumulation | Mild uniform temperature increase |
| 6 | `discoloration` | UV degradation | Patchy mild temperature variation |
| 7 | `normal` | No defect | Uniform temperature distribution |

### Architecture
```
Input: 128-dim feature vector (Stage 2) + cell_anomaly_map
       ↓
[ResNet-18 Backbone]
├─ Residual Block 1 (64 channels)
├─ Residual Block 2 (128 channels)
├─ Residual Block 3 (256 channels)
└─ Residual Block 4 (512 channels)
       ↓
[Attention Pooling]
       ↓
[Transformer Encoder Layer]
├─ Multi-Head Self-Attention (8 heads)
└─ Feed-Forward (512 → 2048 → 512)
       ↓
[Classification Head]
├─ Dense 256 → ReLU → Dropout(0.4)
├─ Dense 128 → ReLU → Dropout(0.3)
└─ Dense 8 → Softmax
       ↓
Output: defect_type_probs (8 classes)
```

### Parameters
- **Model Size:** 45.2 MB
- **FLOPs:** 890M
- **Classes:** 8
- **Format:** ONNX → CoreML / TensorRT

### Input/Output

**Input:**
```json
{
  "cell_features": {...},
  "cell_anomaly_map": "base64_encoded_mask",
  "module_metadata": {
    "manufacturer": "SolarTech",
    "model": "ST-400M",
    "rated_power_w": 400
  }
}
```

**Output:**
```json
{
  "stage": 3,
  "defect_type": "hotspot",
  "defect_type_id": 0,
  "confidence": 0.91,
  "all_probabilities": {
    "hotspot": 0.91,
    "cell_anomaly": 0.05,
    "delamination": 0.02,
    "diode_failure": 0.01,
    "crack": 0.005,
    "soiling": 0.003,
    "discoloration": 0.002,
    "normal": 0.0
  },
  "processing_time_ms": 12.0
}
```

### Training Configuration

```python
# Dataset
- Labeled defects: 25,000 images across 8 classes
- Class distribution: balanced with augmentation

# Hyperparameters
optimizer: AdamW
learning_rate: 1e-4
batch_size: 32
epochs: 100
loss: CrossEntropyLoss(label_smoothing=0.1)

# Augmentation
- Random rotation (±15°)
- Temperature scaling (±10%)
- Noise injection
- Cutout (simulate occlusion)
```

### Performance Metrics

| Defect Type | Precision | Recall | F1 Score |
|-------------|-----------|--------|----------|
| hotspot | 0.96 | 0.94 | 0.95 |
| cell_anomaly | 0.93 | 0.91 | 0.92 |
| delamination | 0.89 | 0.87 | 0.88 |
| diode_failure | 0.97 | 0.95 | 0.96 |
| crack | 0.85 | 0.82 | 0.83 |
| soiling | 0.88 | 0.90 | 0.89 |
| discoloration | 0.84 | 0.86 | 0.85 |
| normal | 0.98 | 0.97 | 0.97 |
| **Overall** | **0.92** | **0.90** | **0.91** |

---

## Stage 4: Severity Scorer

### Purpose
Calculate defect severity, confidence score, and generate actionable recommendations.

### Architecture
```
Input: 
  - defect_type (Stage 3)
  - cell_features (Stage 2)
  - thermal_metadata
  - module_specifications
       ↓
[Feature Fusion Layer]
├─ Concatenate all features
└─ Dense 512 → ReLU
       ↓
[Severity Estimation Branch]
├─ Dense 256 → ReLU
├─ Dense 128 → ReLU
└─ Dense 1 → Sigmoid
       ↓
Severity Score (0.0 - 1.0)
       ↓
[Confidence Calibration Branch]
├─ Dense 128 → ReLU
├─ Uncertainty Estimation (MC Dropout)
└─ Dense 1 → Sigmoid
       ↓
Confidence Score (0.0 - 1.0)
       ↓
[Recommendation Generator]
├─ Rule-based + ML hybrid
└─ Template selection
       ↓
Output: severity, confidence, recommendations
```

### Severity Levels

| Score Range | Level | Action Required |
|-------------|-------|-----------------|
| 0.0 - 0.25 | Low | Monitor, no immediate action |
| 0.25 - 0.50 | Medium | Schedule maintenance within 30 days |
| 0.50 - 0.75 | High | Priority maintenance within 7 days |
| 0.75 - 1.0 | Critical | Immediate action required |

### Input/Output

**Input:**
```json
{
  "defect_type": "hotspot",
  "cell_features": {...},
  "thermal_metadata": {
    "max_temperature": 75.5,
    "ambient_temperature": 35.0,
    "temperature_delta": 40.5,
    "irradiance_w_m2": 850
  },
  "module_specifications": {
    "rated_power_w": 400,
    "temperature_coefficient": -0.0035,
    "max_operating_temp": 85.0
  }
}
```

**Output:**
```json
{
  "stage": 4,
  "severity": {
    "score": 0.82,
    "level": "critical",
    "normalized_temperature_delta": 0.89
  },
  "confidence": {
    "score": 0.94,
    "uncertainty": 0.06,
    "calibration_method": "temperature_scaling"
  },
  "recommendations": [
    {
      "priority": 1,
      "action": "IMMEDIATE_REPLACEMENT",
      "description": "Module shows critical hotspot with 40.5°C temperature delta",
      "estimated_power_loss": "15-20%",
      "safety_risk": "Fire hazard - thermal runaway possible"
    },
    {
      "priority": 2,
      "action": "INSPECT_ADJACENT_MODULES",
      "description": "Check modules in same substring for cascading issues"
    },
    {
      "priority": 3,
      "action": "CHECK_CONNECTIONS",
      "description": "Verify MC4 connectors and wiring integrity"
    }
  ],
  "processing_time_ms": 5.0
}
```

### Training Configuration

```python
# Dataset
- Severity labels: expert-annotated (IEC 62446-3 standard)
- 10,000 samples with severity scores

# Loss Functions
severity_loss: MSELoss
confidence_loss: NLLLoss (calibration)

# Hyperparameters
optimizer: Adam
learning_rate: 1e-3
batch_size: 64
epochs: 50
```

---

## Data Flow Through Pipeline

### Complete Pipeline Execution

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT: Thermal Image                         │
│              640x512 radiometric JPEG (RJPEG)                   │
│                  Temperature: 20°C - 85°C                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: Hotspot Detector                                      │
│  ─────────────────────────                                      │
│  Input: Raw thermal image                                       │
│  Model: Lightweight CNN (2.1 MB)                                │
│  Output: hotspot_detected=true, confidence=0.89                 │
│  Decision: confidence > 0.65 → PASS to Stage 2                  │
│  Time: 2.5ms                                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: Cell Analyzer                                         │
│  ───────────────────                                            │
│  Input: Thermal image + Stage 1 features                        │
│  Model: UNet-based segmentation (18.5 MB)                       │
│  Output: affected_cells=[12,13,22,23], cell_features={...}      │
│  Time: 8.0ms                                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: Module Classifier                                     │
│  ──────────────────────                                         │
│  Input: Cell features + anomaly map                             │
│  Model: ResNet-18 + Transformer (45.2 MB)                       │
│  Output: defect_type="hotspot", confidence=0.91                 │
│  Time: 12.0ms                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 4: Severity Scorer                                       │
│  ───────────────────                                            │
│  Input: Defect type + cell features + metadata                  │
│  Model: Multi-branch network (8.5 MB)                           │
│  Output: severity=0.82 (critical), confidence=0.94              │
│         + recommendations                                       │
│  Time: 5.0ms                                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FINAL OUTPUT                                 │
│  {                                                              │
│    "module_id": "mod_001_05",                                   │
│    "defect_type": "hotspot",                                    │
│    "severity": "critical",                                      │
│    "confidence": 0.94,                                          │
│    "temperature_delta": 40.5,                                   │
│    "affected_cells": [12, 13, 22, 23],                          │
│    "recommendations": [...],                                    │
│    "total_processing_time_ms": 27.5                             │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Model Training Infrastructure

### Hardware Requirements

| Component | Training | Inference (Edge) | Inference (Cloud) |
|-----------|----------|------------------|-------------------|
| GPU | NVIDIA A100 40GB | - | NVIDIA T4 / A10G |
| CPU | 32-core AMD EPYC | Apple M2 | 8-core Intel |
| RAM | 256 GB | 8 GB | 16 GB |
| Storage | 2 TB NVMe | 50 GB SSD | 100 GB SSD |

### Training Pipeline

```python
# training_pipeline.py
from ml_inference.training import ModelTrainer, DataPipeline

# 1. Data Preparation
data_pipeline = DataPipeline(
    data_dir="/data/thermal_images",
    annotations="/data/annotations",
    train_split=0.8,
    val_split=0.1,
    test_split=0.1
)

train_loader = data_pipeline.get_train_loader(batch_size=32)
val_loader = data_pipeline.get_val_loader()

# 2. Model Initialization
trainer = ModelTrainer(
    stage=3,  # Module Classifier
    model_arch="resnet18_transformer",
    num_classes=8,
    pretrained=True
)

# 3. Training Loop
trainer.train(
    train_loader=train_loader,
    val_loader=val_loader,
    epochs=100,
    learning_rate=1e-4,
    callbacks=[
        EarlyStopping(patience=10),
        ModelCheckpoint(save_best_only=True),
        TensorBoardLogger(log_dir="/logs/stage3"),
    ]
)

# 4. Export Models
trainer.export(
    formats=["onnx", "coreml", "torchscript"],
    output_dir="/models/stage3",
    optimize_for=["edge", "cloud"]
)
```

### Dataset Structure

```
/data/
├── thermal_images/
│   ├── site_001/
│   │   ├── insp_001/
│   │   │   ├── mod_001_01.rjpeg
│   │   │   ├── mod_001_01.json  # Metadata
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── annotations/
│   ├── stage1_hotspots.json
│   ├── stage2_cell_masks/
│   ├── stage3_defect_labels.json
│   └── stage4_severity_scores.json
└── splits/
    ├── train.txt
    ├── val.txt
    └── test.txt
```

---

## Model Deployment Pipeline

### Edge Deployment (Mac M2)

```bash
# 1. Convert models to CoreML
python -m ml_inference.export \
  --stage all \
  --format coreml \
  --optimize-for edge \
  --compute-units ALL

# 2. Quantize models (optional, reduces size by 4x)
python -m ml_inference.quantize \
  --stage all \
  --precision int8 \
  --calibration-data /data/calibration_set

# 3. Deploy to edge
scp models/coreml/*.mlmodel edge-device:/opt/doctor-doom/models/

# 4. Validate on edge
ssh edge-device "docker compose restart ml-inference"
```

### Cloud Deployment (GPU)

```bash
# 1. Convert models to TensorRT
python -m ml_inference.export \
  --stage all \
  --format tensorrt \
  --precision fp16 \
  --max-batch-size 8

# 2. Push models to S3
aws s3 sync models/tensorrt/ s3://doctor-doom-models/tensorrt/

# 3. Update SageMaker endpoint
aws sagemaker update-endpoint \
  --endpoint-name ml-inference-prod \
  --model-name ml-inference-v2
```

### Model Versioning

```
/models/
├── v1.0.0/
│   ├── stage1_hotspot_detector.onnx
│   ├── stage2_cell_analyzer.onnx
│   ├── stage3_module_classifier.onnx
│   └── stage4_severity_scorer.onnx
├── v1.1.0/
│   └── ...
└── latest -> v1.1.0/
```

---

## Performance Optimization

### Edge Optimization (Mac M2)

| Technique | Latency Reduction | Size Reduction |
|-----------|-------------------|----------------|
| CoreML Conversion | 40% | - |
| INT8 Quantization | 20% | 75% |
| Model Pruning | 15% | 30% |
| Knowledge Distillation | 10% | 50% |

### Cloud Optimization (GPU)

| Technique | Throughput Increase |
|-----------|---------------------|
| TensorRT FP16 | 2.5x |
| Batch Processing (8x) | 6x |
| Multi-GPU | 15x |
| Model Parallelism | 20x |

---

## Monitoring & Quality Assurance

### Model Performance Metrics

```python
# Track in production
metrics = {
    "inference_latency_p50": 25.0,  # ms
    "inference_latency_p95": 35.0,  # ms
    "inference_latency_p99": 45.0,  # ms
    
    "stage1_confidence_mean": 0.87,
    "stage3_accuracy_estimate": 0.91,
    
    "defect_distribution": {
        "hotspot": 0.35,
        "cell_anomaly": 0.25,
        "delamination": 0.15,
        "diode_failure": 0.10,
        "crack": 0.08,
        "soiling": 0.04,
        "discoloration": 0.03
    },
    
    "severity_distribution": {
        "low": 0.40,
        "medium": 0.35,
        "high": 0.20,
        "critical": 0.05
    }
}
```

### Drift Detection

```python
# Detect data drift
if drift_detected("stage3_input_features"):
    trigger_alert("Model drift detected - retraining recommended")
    queue_retraining_job()
```

---

## API Reference

### Inference Endpoint

```bash
POST /api/v1/ml/infer
Content-Type: application/json
Authorization: Bearer <token>

{
  "image_id": "img_insp_001_mod_005",
  "thermal_data": "base64_encoded_rjpeg",
  "module_id": "mod_001_05",
  "inspection_id": "insp_001",
  "metadata": {
    "ambient_temp": 35.0,
    "irradiance": 850,
    "module_model": "ST-400M"
  }
}

# Response (200 OK)
{
  "status": "success",
  "result": {
    "module_id": "mod_001_05",
    "defect_type": "hotspot",
    "severity": "critical",
    "confidence": 0.94,
    "temperature_delta": 40.5,
    "affected_cells": [12, 13, 22, 23],
    "recommendations": [...],
    "stage_times": {
      "stage1": 2.5,
      "stage2": 8.0,
      "stage3": 12.0,
      "stage4": 5.0
    },
    "total_time_ms": 27.5
  }
}
```

### Batch Inference

```bash
POST /api/v1/ml/infer/batch
Content-Type: application/json

{
  "images": [
    {"image_id": "img_001", "thermal_data": "..."},
    {"image_id": "img_002", "thermal_data": "..."},
    ...
  ],
  "max_batch_size": 8
}

# Response
{
  "status": "success",
  "results": [...],
  "batch_processing_time_ms": 125.0,
  "avg_time_per_image_ms": 15.6
}
```

---

## Troubleshooting

### Common Issues

**Issue: High latency on edge**
```bash
# Check model optimization
ls -lh /opt/doctor-doom/models/*.mlmodel

# Verify CoreML compute units
python -c "import coremltools as ct; print(ct.utils.get_spec('/path/to/model.mlmodel'))"

# Solution: Re-export with ALL compute units
python -m ml_inference.export --compute-units ALL
```

**Issue: Low confidence scores**
```python
# Check calibration
from ml_inference.calibration import TemperatureScaling

scaler = TemperatureScaling.load('/models/calibration.pkl')
calibrated_probs = scaler.predict(raw_probs)
```

**Issue: Model drift**
```bash
# Trigger retraining
make retrain-models STAGE=3 DATA=/data/new_samples

# Validate new model
make validate-model MODEL=/models/v1.2.0/stage3.onnx
```

---

## References

1. IEC 62446-3:2017 - Photovoltaic module inspection guidelines
2. Redmon, J. et al. "You Only Look Once" (YOLO) for defect detection
3. Ronneberger, O. et al. "U-Net: Convolutional Networks for Biomedical Image Segmentation"
4. He, K. et al. "Deep Residual Learning for Image Recognition" (ResNet)
5. Vaswani, A. et al. "Attention Is All You Need" (Transformer)
