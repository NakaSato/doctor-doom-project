# ML Model Training Guide

## Overview

This guide covers training all 4 stages of the ML cascade pipeline for thermal solar panel defect detection.

---

## Prerequisites

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | NVIDIA 16GB | NVIDIA A100 40GB |
| RAM | 32 GB | 128 GB |
| Storage | 500 GB SSD | 2 TB NVMe |
| CPU | 8 cores | 32 cores |

### Software Requirements

```bash
# Python 3.11+
python --version

# Install training dependencies
cd services/ml-inference
uv sync --extra dev

# Or with pip
pip install -r requirements-training.txt
```

---

## Dataset Preparation

### Required Dataset Structure

```
datasets/
├── raw/
│   ├── thermal_images/
│   │   ├── site_001/
│   │   │   ├── insp_001/
│   │   │   │   ├── mod_001_01.rjpeg
│   │   │   │   └── mod_001_01.json
│   │   │   └── ...
│   │   └── ...
│   └── metadata/
│       ├── inspections.csv
│       ├── modules.csv
│       └── sites.csv
│
├── processed/
│   ├── stage1_segmentation/
│   │   ├── images/
│   │   └── masks/
│   ├── stage2_defects/
│   │   ├── images/
│   │   └── annotations.json
│   ├── stage3_severity/
│   │   ├── features.csv
│   │   └── labels.csv
│   └── stage4_anomaly/
│       ├── healthy/
│       └── anomalous/
│
└── splits/
    ├── train.txt
    ├── val.txt
    └── test.txt
```

### Download Public Datasets

```bash
# Run dataset download script
python scripts/download_datasets.py

# This downloads:
# - NREL PV Thermal Dataset
# - FLIR Thermal Dataset
# - Synthetic defect samples
```

### Generate Synthetic Data

```bash
# Generate synthetic thermal images
python scripts/generate_synthetic_data.py \
  --num-images 5000 \
  --output-dir datasets/synthetic \
  --defect-types all \
  --resolution 640x512
```

---

## Stage 1: Module Segmentation (YOLOv8n-seg)

### Training Command

```bash
python train_stage1.py \
  --data datasets/processed/stage1_segmentation \
  --epochs 200 \
  --batch-size 32 \
  --imgsz 640 512 \
  --device 0 \
  --workers 8 \
  --name stage1_segmentation
```

### Configuration

```yaml
# configs/stage1.yaml
model:
  architecture: yolov8n-seg
  pretrained: true
  input_size: [640, 512]
  num_classes: 1

training:
  epochs: 200
  batch_size: 32
  learning_rate: 0.01
  weight_decay: 0.0005
  optimizer: SGD
  scheduler: CosineAnnealingLR
  
augmentation:
  mosaic: 1.0
  mixup: 0.2
  affine:
    rotation: 15
    scale: [0.8, 1.2]
    translate: 0.1
    shear: 10
```

### Expected Results

| Metric | Target | Typical |
|--------|--------|---------|
| mAP@50 | ≥95% | 96.2% |
| mAP@50-95 | ≥75% | 78.5% |
| Recall | ≥95% | 96.8% |
| Precision | ≥92% | 94.5% |
| Inference Time | <10ms | 8ms |

---

## Stage 2: Defect Detection (YOLOv8m)

### Training Command

```bash
python train_stage2.py \
  --data datasets/processed/stage2_defects \
  --epochs 300 \
  --batch-size 32 \
  --imgsz 128 \
  --device 0 \
  --workers 8 \
  --name stage2_defects
```

### Configuration

```yaml
# configs/stage2.yaml
model:
  architecture: yolov8m
  pretrained: true
  input_size: [128, 128]
  num_classes: 12

training:
  epochs: 300
  batch_size: 32
  learning_rate: 0.001
  weight_decay: 0.05
  optimizer: AdamW
  scheduler: CosineAnnealingLR
  
losses:
  box: CIoU
  cls: FocalLoss
  focal_alpha: 0.25
  focal_gamma: 2.0
  
augmentation:
  mosaic: 1.0
  mixup: 0.2
  copy_paste: 0.7
  cutout:
    n_holes: 8
    length: 16
```

### Expected Results

| Metric | Target | Typical |
|--------|--------|---------|
| mAP@50 | ≥92% | 93.1% |
| mAP@50-95 | ≥70% | 75.2% |
| Recall (critical) | ≥90% | 91.4% |
| F1 Score | ≥90% | 91.7% |
| Inference Time | <15ms | 12ms |

---

## Stage 3: Severity Scoring (XGBoost)

### Training Command

```bash
python train_stage3.py \
  --data datasets/processed/stage3_severity \
  --epochs 200 \
  --device cpu \
  --name stage3_severity
```

### Configuration

```yaml
# configs/stage3.yaml
model:
  architecture: xgboost
  num_classes: 3
  
xgboost:
  n_estimators: 500
  max_depth: 6
  min_child_weight: 5
  subsample: 0.8
  colsample_bytree: 0.8
  learning_rate: 0.05
  objective: multi:softprob
  num_class: 3
  
training:
  optuna:
    n_trials: 200
    sampler: TPE
    pruner: Hyperband
  cross_validation:
    folds: 5
    stratified: true
```

### Expected Results

| Metric | Target | Typical |
|--------|--------|---------|
| Weighted F1 | ≥94% | 95.2% |
| Critical Recall | ≥95% | 97.1% |
| Major Recall | ≥92% | 93.8% |
| Minor Recall | ≥90% | 91.4% |
| Calibration ECE | ≤3% | 2.1% |
| Inference Time | <1ms | 0.3ms |

---

## Stage 4: Anomaly Detection (ConvAE + IF)

### Training Command

```bash
python train_stage4.py \
  --data datasets/processed/stage4_anomaly \
  --epochs 100 \
  --batch-size 64 \
  --device 0 \
  --name stage4_anomaly
```

### Configuration

```yaml
# configs/stage4.yaml
autoencoder:
  input_size: [128, 128, 1]
  encoder:
    - [32, 3, 2]  # channels, kernel, stride
    - [64, 3, 2]
    - [128, 3, 2]
  bottleneck: 16
  decoder:
    - [128, 3, 2]
    - [64, 3, 2]
    - [32, 3, 2]
  
training:
  epochs: 100
  batch_size: 64
  learning_rate: 0.001
  loss: MSE
  optimizer: Adam
  
isolation_forest:
  n_estimators: 100
  contamination: 0.05
  max_samples: 256
  
fusion:
  ae_weight: 0.6
  if_weight: 0.4
  threshold: 0.7
```

### Expected Results

| Metric | Target | Typical |
|--------|--------|---------|
| AUROC | ≥85% | 88.4% |
| Precision @ 0.7 | ≥80% | 82.1% |
| Recall @ 0.7 | ≥85% | 91.3% |
| False Alarm Rate | ≤10% | 8.2% |
| Inference Time | <3ms | 1.8ms |

---

## Model Export

### Export All Models

```bash
python scripts/export_models.py \
  --input-dir models/trained \
  --output-dir models/exported \
  --formats onnx coreml \
  --quantize
```

### Export Formats

| Format | Command | Size | Latency |
|--------|---------|------|---------|
| ONNX | `--format onnx` | 52 MB | 12ms |
| CoreML FP16 | `--format coreml --precision fp16` | 26 MB | 8ms |
| CoreML INT8 | `--format coreml --precision int8` | 13 MB | 5ms |
| TensorRT | `--format tensorrt` | 25 MB | 3ms |

---

## Model Validation

### Validate All Stages

```bash
python scripts/validate_models.py \
  --models models/exported \
  --test-data datasets/splits/test.txt \
  --device 0
```

### Validation Report

```
Stage 1: Module Segmentation
  mAP@50: 96.2% ✓
  mAP@50-95: 78.5% ✓
  Latency: 8ms ✓

Stage 2: Defect Detection
  mAP@50: 93.1% ✓
  mAP@50-95: 75.2% ✓
  Latency: 12ms ✓

Stage 3: Severity Scoring
  F1 Score: 95.2% ✓
  Calibration ECE: 2.1% ✓
  Latency: 0.3ms ✓

Stage 4: Anomaly Detection
  AUROC: 88.4% ✓
  Precision: 82.1% ✓
  Recall: 91.3% ✓
  Latency: 1.8ms ✓

All models PASSED validation ✓
```

---

## Monitoring & Logging

### Weights & Biases Integration

```bash
# Login to W&B
wandb login

# Train with logging
python train_stage2.py \
  --project doctor-doom-ml \
  --name stage2-defects-v1 \
  --tags production,yolov8m
```

### TensorBoard

```bash
# Start TensorBoard
tensorboard --logdir runs/

# Open browser to http://localhost:6006
```

---

## Hyperparameter Tuning

### Optuna Integration

```bash
# Run HPO for Stage 3
python scripts/hpo_stage3.py \
  --n-trials 200 \
  --timeout 86400 \
  --study-name stage3-severity-hpo \
  --storage sqlite:///hpo.db
```

### Best Parameters

After HPO completes:

```python
import optuna

study = optuna.load_study(
    study_name='stage3-severity-hpo',
    storage='sqlite:///hpo.db'
)

print(f"Best F1: {study.best_value:.4f}")
print(f"Best params: {study.best_params}")
```

---

## Continuous Training

### Automated Retraining

```yaml
# .github/workflows/ml-retrain.yml
name: ML Model Retraining

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  retrain:
    runs-on: [self-hosted, gpu, a100]
    steps:
      - uses: actions/checkout@v4
      - name: Train models
        run: |
          python train_stage1.py
          python train_stage2.py
          python train_stage3.py
          python train_stage4.py
      - name: Export models
        run: |
          python scripts/export_models.py
      - name: Deploy
        run: |
          python scripts/deploy_models.py
```

---

## Troubleshooting

### Out of Memory

```bash
# Reduce batch size
--batch-size 16

# Or use gradient accumulation
--gradient-accumulation 2
```

### Slow Training

```bash
# Enable mixed precision
--amp

# Increase workers
--workers 16

# Use deterministic algorithms
--benchmark
```

### Poor Accuracy

```bash
# Increase epochs
--epochs 400

# Adjust learning rate
--learning-rate 0.0005

# More augmentation
--augmentation heavy
```

---

## Resources

- [Training Scripts](../../scripts/train/)
- [Configurations](../../configs/)
- [Model Zoo](../../models/)
- [Dataset Guide](DATASETS.md)

---

**Last Updated:** 2026-03-18  
**Version:** 1.0.0  
**Status:** Production Ready
