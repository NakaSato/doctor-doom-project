# ML Training Infrastructure

## Overview

This document describes the training infrastructure for the four-stage ML cascade pipeline.

## Hardware Setup

### Training Cluster

```yaml
# Training Hardware Configuration
gpu_nodes:
  - count: 4
    gpu: NVIDIA A100 40GB
    cpu: AMD EPYC 7763 (64 cores)
    ram: 512 GB
    storage: 4 TB NVMe
    interconnect: NVIDIA NVLink

storage:
  - type: NAS
    capacity: 100 TB
    protocol: NFS
    use: Dataset storage
    
  - type: Object Storage
    capacity: 500 TB
    protocol: S3
    use: Model artifacts, checkpoints
```

### Local Development (Mac M2)

```yaml
# For fine-tuning and testing
device: Mac Studio / MacBook Pro M2
gpu: Apple Silicon (10-core GPU)
ram: 32-64 GB unified memory
storage: 1 TB SSD
framework: CoreML Tools
```

## Dataset Structure

### Raw Data Organization

```
/datasets/
├── raw/
│   ├── thermal_images/
│   │   ├── site_001/
│   │   │   ├── insp_2024_001/
│   │   │   │   ├── mod_001_01.rjpeg
│   │   │   │   ├── mod_001_01.json
│   │   │   │   └── ...
│   │   │   └── ...
│   │   └── ...
│   └── metadata/
│       ├── inspections.csv
│       ├── modules.csv
│       └── sites.csv
│
├── processed/
│   ├── stage1_hotspots/
│   │   ├── positive/
│   │   └── negative/
│   ├── stage2_cells/
│   │   ├── masks/
│   │   └── features/
│   ├── stage3_defects/
│   │   └── annotations.json
│   └── stage4_severity/
│       └── scores.json
│
└── splits/
    ├── train.txt (80%)
    ├── val.txt (10%)
    └── test.txt (10%)
```

### Annotation Formats

**Stage 1 (Hotspot Detection):**
```json
{
  "image_id": "mod_001_01",
  "label": "hotspot",
  "confidence": 0.95,
  "annotator": "expert_001",
  "timestamp": "2024-08-15T10:30:00Z"
}
```

**Stage 2 (Cell Segmentation):**
```json
{
  "image_id": "mod_001_01",
  "cell_layout": {"rows": 6, "cols": 10},
  "cells": [
    {
      "cell_id": 12,
      "position": [2, 2],
      "mask": "base64_encoded_polygon",
      "anomaly": true,
      "temp_delta": 15.2
    }
  ]
}
```

**Stage 3 (Defect Classification):**
```json
{
  "image_id": "mod_001_01",
  "defect_type": "hotspot",
  "confidence": 0.91,
  "expert_verified": true,
  "iec_code": "IEC-62446-3-HS-001"
}
```

**Stage 4 (Severity Scoring):**
```json
{
  "image_id": "mod_001_01",
  "severity_score": 0.82,
  "severity_level": "critical",
  "power_loss_estimate": 0.18,
  "recommendation": "IMMEDIATE_REPLACEMENT"
}
```

## Training Pipeline

### Stage 1: Hotspot Detector

```bash
# Training command
python -m ml_inference.train stage1 \
  --data-dir /datasets/processed/stage1_hotspots \
  --splits /datasets/splits \
  --output-dir /models/stage1 \
  --batch-size 64 \
  --epochs 50 \
  --learning-rate 1e-3 \
  --device cuda \
  --num-workers 8
```

**Configuration:**
```yaml
# configs/stage1.yaml
model:
  architecture: MobileNetV3-Small
  input_size: [640, 512]
  num_classes: 2
  
training:
  optimizer: AdamW
  learning_rate: 0.001
  weight_decay: 0.01
  batch_size: 64
  epochs: 50
  
  scheduler:
    type: CosineAnnealingLR
    T_max: 50
    eta_min: 1e-6
  
  augmentation:
    - RandomRotation: ±15°
    - HorizontalFlip: p=0.5
    - VerticalFlip: p=0.5
    - ColorJitter: brightness=0.2
    - GaussianNoise: σ=0.01
  
  class_weights:
    positive: 1.67
    negative: 1.0

validation:
  metrics:
    - accuracy
    - precision
    - recall
    - f1
    - roc_auc
  early_stopping:
    patience: 10
    min_delta: 0.001
```

### Stage 2: Cell Analyzer

```bash
# Training command
python -m ml_inference.train stage2 \
  --data-dir /datasets/processed/stage2_cells \
  --splits /datasets/splits \
  --output-dir /models/stage2 \
  --batch-size 16 \
  --epochs 80 \
  --learning-rate 5e-4 \
  --device cuda \
  --num-workers 4 \
  --pretrained /models/stage1/best.onnx
```

**Configuration:**
```yaml
# configs/stage2.yaml
model:
  architecture: UNet-ResNet34
  input_size: [640, 512]
  num_cells: 60
  feature_dim: 128
  
training:
  optimizer: AdamW
  learning_rate: 0.0005
  weight_decay: 0.01
  batch_size: 16
  epochs: 80
  
  losses:
    segmentation:
      - DiceLoss: weight=1.0
      - BCELoss: weight=0.5
    features:
      - ContrastiveLoss: weight=0.3
  
  augmentation:
    - RandomRotation: ±10°
    - ElasticTransform: alpha=50, sigma=5
    - ScaleJitter: 0.9-1.1
```

### Stage 3: Module Classifier

```bash
# Training command
python -m ml_inference.train stage3 \
  --data-dir /datasets/processed/stage3_defects \
  --splits /datasets/splits \
  --output-dir /models/stage3 \
  --batch-size 32 \
  --epochs 100 \
  --learning-rate 1e-4 \
  --device cuda \
  --num-workers 8 \
  --pretrained imagenet
```

**Configuration:**
```yaml
# configs/stage3.yaml
model:
  architecture: ResNet18-Transformer
  backbone: ResNet18
  transformer_layers: 2
  num_heads: 8
  num_classes: 8
  
training:
  optimizer: AdamW
  learning_rate: 0.0001
  weight_decay: 0.05
  batch_size: 32
  epochs: 100
  
  scheduler:
    type: ReduceLROnPlateau
    factor: 0.5
    patience: 5
    min_lr: 1e-6
  
  label_smoothing: 0.1
  
  augmentation:
    - RandomRotation: ±15°
    - Cutout: n_holes=5, length=32
    - Mixup: alpha=0.4
    - TemperatureScaling: ±10%

validation:
  metrics:
    - accuracy
    - precision_per_class
    - recall_per_class
    - f1_per_class
    - confusion_matrix
```

### Stage 4: Severity Scorer

```bash
# Training command
python -m ml_inference.train stage4 \
  --data-dir /datasets/processed/stage4_severity \
  --splits /datasets/splits \
  --output-dir /models/stage4 \
  --batch-size 64 \
  --epochs 50 \
  --learning-rate 1e-3 \
  --device cuda \
  --num-workers 8
```

**Configuration:**
```yaml
# configs/stage4.yaml
model:
  architecture: MultiBranchNetwork
  feature_dim: 512
  num_branches: 3  # severity, confidence, recommendations
  
training:
  optimizer: Adam
  learning_rate: 0.001
  weight_decay: 0.01
  batch_size: 64
  epochs: 50
  
  losses:
    severity: MSELoss
    confidence: NLLLoss
    recommendations: CrossEntropyLoss
  
  calibration:
    method: TemperatureScaling
    validation_split: 0.2
```

## Distributed Training

### Multi-GPU Setup

```bash
# 4-GPU training
torchrun \
  --nproc_per_node=4 \
  --nnodes=1 \
  --node_rank=0 \
  --master_addr="localhost" \
  --master_port=29500 \
  -m ml_inference.train stage3 \
  --distributed \
  --batch-size 128  # 32 per GPU
```

### Multi-Node Setup

```bash
# Node 0 (master)
torchrun \
  --nproc_per_node=4 \
  --nnodes=2 \
  --node_rank=0 \
  --master_addr="node0.cluster" \
  --master_port=29500 \
  -m ml_inference.train stage3 \
  --distributed

# Node 1
torchrun \
  --nproc_per_node=4 \
  --nnodes=2 \
  --node_rank=1 \
  --master_addr="node0.cluster" \
  --master_port=29500 \
  -m ml_inference.train stage3 \
  --distributed
```

## Model Export

### Export to Multiple Formats

```bash
# Export all stages
python -m ml_inference.export \
  --model-dir /models \
  --output-dir /models/exported \
  --formats onnx coreml torchscript \
  --optimize-for edge cloud
```

### CoreML Export (Edge)

```python
# export_coreml.py
import coremltools as ct
import torch

# Load model
model = torch.load('stage1.pth')
model.eval()

# Trace model
example_input = torch.rand(1, 1, 640, 512)
traced_model = torch.jit.trace(model, example_input)

# Convert to CoreML
mlmodel = ct.convert(
    traced_model,
    inputs=[ct.ImageType(shape=example_input.shape, scale=1/255.0)],
    convert_to="mlprogram",  # MLProgram format
    compute_units=ct.ComputeUnit.ALL  # Use all compute units
)

# Save
mlmodel.save('stage1_hotspot_detector.mlmodel')
```

### TensorRT Export (Cloud)

```python
# export_tensorrt.py
import torch
import tensorrt as trt

# Load ONNX model
onnx_path = 'stage1.onnx'

# Create TensorRT engine
logger = trt.Logger(trt.Logger.WARNING)
builder = trt.Builder(logger)
network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
parser = trt.OnnxParser(network, logger)

# Parse ONNX
with open(onnx_path, 'rb') as f:
    parser.parse(f.read())

# Build engine
config = builder.create_builder_config()
config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 4 << 30)  # 4GB
config.set_flag(trt.BuilderFlag.FP16)  # Enable FP16

engine = builder.build_engine(network, config)

# Save engine
with open('stage1.trt', 'wb') as f:
    f.write(engine.serialize())
```

## Model Quantization

### Post-Training Quantization (INT8)

```python
# quantize.py
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType

# Quantize model
quantize_dynamic(
    model_input='stage1.onnx',
    model_output='stage1_quantized.onnx',
    weight_type=QuantType.QUInt8,
    per_channel=True,
    reduce_range=False
)

# Result: 4x size reduction, minimal accuracy loss
```

### Quantization-Aware Training

```python
# qat_training.py
import torch
import torch.quantization as quant

# Prepare model for QAT
model = get_model()
model.qconfig = torch.quantization.get_default_qat_qconfig('fbgemm')
model_prepared = torch.quantization.prepare_qat(model)

# Train with quantization simulation
train(model_prepared, ...)

# Convert to quantized model
model_quantized = torch.quantization.convert(model_prepared)
```

## Experiment Tracking

### Weights & Biases Integration

```python
# training.py
import wandb

# Initialize
wandb.init(
    project="doctor-doom-ml",
    name="stage3-resnet18-transformer-v1",
    config={
        "architecture": "ResNet18-Transformer",
        "batch_size": 32,
        "learning_rate": 1e-4,
        "epochs": 100
    }
)

# Log metrics
for epoch in range(epochs):
    train_loss = train_one_epoch(...)
    val_metrics = validate(...)
    
    wandb.log({
        "epoch": epoch,
        "train_loss": train_loss,
        "val_accuracy": val_metrics["accuracy"],
        "val_f1": val_metrics["f1"]
    })

# Log model artifact
wandb.save("best_model.onnx")
wandb.finish()
```

## Continuous Training

### Automated Retraining Pipeline

```yaml
# .github/workflows/ml-retrain.yml
name: ML Model Retraining

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday 2 AM
  workflow_dispatch:
    inputs:
      stage:
        description: 'Stage to retrain (1-4)'
        required: true
        default: 'all'

jobs:
  retrain:
    runs-on: [self-hosted, gpu, a100]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup environment
        run: |
          pip install -r requirements-training.txt
      
      - name: Download latest data
        run: |
          aws s3 sync s3://doctor-doom-data/latest /datasets/raw
      
      - name: Preprocess data
        run: |
          python -m ml_inference.preprocess \
            --input /datasets/raw \
            --output /datasets/processed
      
      - name: Train models
        run: |
          python -m ml_inference.train all \
            --config configs/ \
            --output /models/trained
      
      - name: Evaluate models
        run: |
          python -m ml_inference.evaluate \
            --models /models/trained \
            --test-set /datasets/splits/test.txt
      
      - name: Upload models
        if: success()
        run: |
          aws s3 sync /models/trained s3://doctor-doom-models/v$(date +%Y%m%d)
```

## Performance Benchmarks

### Training Time

| Stage | Dataset Size | GPU | Batch Size | Time/Epoch | Total Time |
|-------|-------------|-----|------------|------------|------------|
| 1 | 40,000 | A100 | 64 | 2 min | 1.7 hours |
| 2 | 8,000 | A100 | 16 | 8 min | 10.7 hours |
| 3 | 25,000 | A100 | 32 | 5 min | 8.3 hours |
| 4 | 10,000 | A100 | 64 | 1 min | 0.8 hours |

### Inference Performance

| Stage | Edge (M2) | Cloud (T4) | Cloud (A10G) |
|-------|-----------|------------|--------------|
| 1 | 2.5ms | 0.8ms | 0.5ms |
| 2 | 8.0ms | 2.5ms | 1.8ms |
| 3 | 12.0ms | 4.0ms | 3.0ms |
| 4 | 5.0ms | 1.5ms | 1.0ms |
| **Total** | **27.5ms** | **8.8ms** | **6.3ms** |

## Troubleshooting

### Common Issues

**Issue: Out of memory during training**
```bash
# Reduce batch size
--batch-size 16  # Instead of 32

# Or use gradient accumulation
--gradient-accumulation-steps 2  # Effective batch = 16 * 2 = 32
```

**Issue: Slow data loading**
```bash
# Increase workers
--num-workers 8

# Use pinned memory
--pin-memory

# Use persistent workers
--persistent-workers
```

**Issue: Model not converging**
```bash
# Check learning rate
--learning-rate 1e-4  # Try lower LR

# Enable gradient clipping
--max-grad-norm 1.0

# Use warmup
--warmup-epochs 5
```
