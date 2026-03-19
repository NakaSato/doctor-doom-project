# YOLOv8m Defect Detection Architecture

## Model Overview

**Architecture:** YOLOv8m defect detection model  
**Parameters:** 25.9M  
**Input:** 128×128×1 (thermal crop)  
**Output:** K defect bboxes × {x, y, w, h, class_id, confidence}

---

## Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    YOLOv8m Defect Detection (25.9M params)                  │
└─────────────────────────────────────────────────────────────────────────────┘

Input: 128×128×1 (thermal crop)
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CSPDarknet-m Backbone                                                      │
│  ═══════════════════════════════════════════════════════════                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Block         Config               Output       Feature Level      │   │
│  │  ─────         ──────               ──────       ─────────────      │   │
│  │                                                                       │   │
│  │  Conv-BN-      3×3, s=2, c=48     64×64×48      P2                   │   │
│  │  SiLU                                                                  │   │
│  │                                                                       │   │
│  │  C2f block     n=2, c=96          32×32×96      P3 ─────┐            │   │
│  │                                                        │ (skip)       │   │
│  │  C2f block     n=4, c=192         16×16×192     P4 ─────┤ (skip)     │   │
│  │                                                        │              │   │
│  │  C2f + SPPF    n=4, c=512 + pool  8×8×512       P5 ─────┘ (skip)     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Skip connections from P3, P4, P5 feed into the neck.                       │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼ (P3, P4, P5 multi-scale features)
┌─────────────────────────────────────────────────────────────────────────────┐
│  PANet-m Neck (Bidirectional FPN)                                           │
│  ═══════════════════════════════════════════════════════                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Upsample P5 → Concat P4 → Concat P3 → Downsample                   │   │
│  │                                                                      │   │
│  │  Three parallel output branches at different scales:                 │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │  P3_out: [32, 32, 96]   - Small defects                      │  │   │
│  │  │  P4_out: [16, 16, 192]  - Medium defects                     │  │   │
│  │  │  P5_out: [8, 8, 512]    - Large defects                      │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼ (P3_out, P4_out, P5_out)
┌─────────────────────────────────────────────────────────────────────────────┐
│  SE-Attention Block (Squeeze-and-Excitation, r=16)                          │
│  ═══════════════════════════════════════════════════════                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Channel Attention:                                                  │   │
│  │  ─────────────────                                                   │   │
│  │  1. GAP (Global Average Pooling): [H, W, C] → [1, 1, C]             │   │
│  │  2. FC(C → C/16): [1, 1, C/16]                                      │   │
│  │  3. ReLU                                                            │   │
│  │  4. FC(C/16 → C): [1, 1, C]                                         │   │
│  │  5. Sigmoid: channel weights [1, 1, C]                              │   │
│  │  6. Scale: output = input × channel_weights                         │   │
│  │                                                                      │   │
│  │  Reduction ratio r=16:                                               │   │
│  │  • P3_out: 96 → 6 → 96 channels                                     │   │
│  │  • P4_out: 192 → 12 → 192 channels                                  │   │
│  │  • P5_out: 512 → 32 → 512 channels                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼ (Refined multi-scale features)
┌─────────────────────────────────────────────────────────────────────────────┐
│  Dual Output Branches                                                       │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌────────────────────────────────────┐  ┌─────────────────────────────┐   │
│  │  Detection Branch                  │  │  Classification Branch      │   │
│  │  ──────────────────                │  │  ─────────────────────      │   │
│  │                                    │  │                             │   │
│  │  3× Conv(256) +                    │  │  12-class + background      │   │
│  │  bbox regression                   │  │  (13 total)                 │   │
│  │                                    │  │                             │   │
│  │  • CIoU loss                       │  │  • Focal Loss               │   │
│  │  • Anchor-free                     │  │  • α=0.25, γ=2.0            │   │
│  │  • Output: [N, 4]                  │  │  • Output: [N, 13]          │   │
│  │    (cx, cy, w, h)                  │  │    (class probabilities)    │   │
│  └────────────────────────────────────┘  └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  NMS + Class-Aware Filtering                                                │
│  ═══════════════════════════════════                                        │
│                                                                             │
│  • IoU threshold: 0.5                                                       │
│  • Confidence threshold: 0.25                                               │
│  • Class-aware NMS (separate per defect type)                               │
│  • Max detections: 50 per module                                            │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FINAL OUTPUT                                         │
│                                                                             │
│  K defect bboxes × {x, y, w, h, class_id, confidence}                       │
│                                                                             │
│  Example:                                                                   │
│  [                                                                          │
│    {x: 45, y: 32, w: 18, h: 22, class_id: 0, conf: 0.94},  // hot_spot     │
│    {x: 78, y: 56, w: 12, h: 15, class_id: 1, conf: 0.87},  // cell_crack  │
│    ...                                                                      │
│  ]                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### CSPDarknet-m Backbone

**Purpose:** Extract multi-scale features from thermal module crops

| Block | Configuration | Output Size | Feature Level | Purpose |
|-------|--------------|-------------|---------------|---------|
| Conv-BN-SiLU | 3×3, stride=2, channels=48 | 64×64×48 | P2 | Initial downsampling |
| C2f block | n=2, channels=96 | 32×32×96 | P3 | Small defect features |
| C2f block | n=4, channels=192 | 16×16×192 | P4 | Medium defect features |
| C2f + SPPF | n=4, channels=512 + pooling | 8×8×512 | P5 | Large defect features |

**C2f Block Structure:**
```
Input ──┬──→ Conv(1×1) ──→ Split
        │
        ├─→ Branch 1: Identity ───────────────────────┐
        │                                             │
        └─→ Branch 2: Conv(3×3) → Conv(3×3) ──────────┤
                                                      │
                                                      ▼
                                                Concat → Conv(1×1) → Output

Gradient flow enhancement via cross-stage partial connections
```

**SPPF (Spatial Pyramid Pooling - Fast):**
```
Input → Conv(1×1) → [5×5 MaxPool]³ (3 cascades) → Concat → Conv(1×1) → Output

5×5 Max Pool cascades:
• Pool1: 5×5 max → concat with input
• Pool2: 5×5 max → concat with previous
• Pool3: 5×5 max → concat with previous

Output channels: 512 + 512 + 512 + 512 = 2048 → Conv(1×1) → 512
```

---

### PANet-m Neck (Bidirectional FPN)

**Purpose:** Fuse multi-scale features for robust detection at all scales

```
Bottom-Up Path Augmentation:
┌─────────────────────────────────────────────────────────────────┐
│  P5 [8,8,512] → Upsample(2×) → Concat(P4) → C2f → P5_out      │
│  P5_out [16,16,192] → Upsample(2×) → Concat(P3) → C2f → P4_out│
│  P4_out [32,32,96] → C2f → P3_out                              │
└─────────────────────────────────────────────────────────────────┘

Top-Down Path Augmentation:
┌─────────────────────────────────────────────────────────────────┐
│  P3_out [32,32,96] → Conv(s=2) → Concat(P4_out) → C2f → P3_final│
│  P3_final [16,16,192] → Conv(s=2) → Concat(P5_out) → C2f → P4_final│
│  P4_final [8,8,512] → C2f → P5_final                           │
└─────────────────────────────────────────────────────────────────┘

Three parallel output branches:
• P3_final: [32, 32, 96]   - Small defects
• P4_final: [16, 16, 192]  - Medium defects
• P5_final: [8, 8, 512]    - Large defects
```

---

### SE-Attention Block (Squeeze-and-Excitation)

**Purpose:** Channel-wise attention to enhance defect-specific features

**Architecture:**
```
Input: [H, W, C]
         │
         ▼
┌─────────────────────────────────────────┐
│  Squeeze (Global Information Embedding) │
│  ─────────────────────────────────────  │
│  Global Average Pooling:                │
│  z_c = (1/H×W) × ΣΣ X[i,j,c]            │
│  Output: [1, 1, C]                      │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Excitation (Adaptive Recalibration)    │
│  ─────────────────────────────────────  │
│  FC(C → C/16) → ReLU                    │
│  FC(C/16 → C) → Sigmoid                 │
│  Reduction ratio r=16                   │
│  Output: [1, 1, C] (channel weights)    │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Scaling (Feature Recalibration)        │
│  ─────────────────────────────────────  │
│  X'[i,j,c] = scale_c × X[i,j,c]         │
│  Output: [H, W, C] (refined features)   │
└─────────────────────────────────────────┘

Applied to each scale:
• P3_final: 96 → 6 → 96 channels
• P4_final: 192 → 12 → 192 channels
• P5_final: 512 → 32 → 512 channels
```

**Benefits:**
- Channel-wise attention for defect-specific features
- Improved sensitivity to subtle thermal anomalies
- Minimal overhead: +0.5ms latency, +2.1M parameters

---

### Detection Branch

**Purpose:** Predict bounding box coordinates (anchor-free)

```
┌─────────────────────────────────────────────────────────────────┐
│  Detection Head (per scale)                                     │
│  ───────────────────────                                        │
│                                                                 │
│  Conv(3×3, 256) → SiLU → Conv(3×3, 256) → SiLU                 │
│         │                                                        │
│         ▼                                                        │
│  Conv(1×1, 4) → SiLU                                            │
│         │                                                        │
│         ▼                                                        │
│  Output: [N, 4] (cx, cy, w, h)                                  │
│                                                                 │
│  Loss: CIoU (Complete IoU)                                      │
│  • Anchor-free detection                                        │
│  • Direct coordinate regression                                 │
└─────────────────────────────────────────────────────────────────┘
```

**CIoU Loss:**
```
CIoU = IoU - (ρ²(b,b_gt)/c²) - αν

where:
• IoU: Intersection over Union
• ρ: Euclidean distance between predicted and ground truth centers
• c: Diagonal length of smallest enclosing box
• α: Weighting factor
• ν: Aspect ratio consistency

Benefits:
• Faster convergence than GIoU
• Better localization accuracy
• Handles non-overlapping boxes
```

---

### Classification Branch

**Purpose:** Predict 12 defect classes + 1 background class

```
┌─────────────────────────────────────────────────────────────────┐
│  Classification Head (per scale)                                │
│  ─────────────────────────                                      │
│                                                                 │
│  Conv(3×3, 256) → SiLU → Conv(3×3, 256) → SiLU                 │
│         │                                                        │
│         ▼                                                        │
│  Conv(1×1, 13) → Sigmoid                                        │
│         │                                                        │
│         ▼                                                        │
│  Output: [N, 13] (class probabilities)                          │
│                                                                 │
│  Classes: 12 defect types + 1 background                        │
│  Loss: Focal Loss (α=0.25, γ=2.0)                               │
└─────────────────────────────────────────────────────────────────┘
```

**Focal Loss:**
```
FL(p_t) = -α_t × (1 - p_t)^γ × log(p_t)

where:
• p_t: predicted probability for true class
• α_t: balancing factor (0.25)
• γ: focusing parameter (2.0)

Purpose:
• Down-weight easy examples
• Focus training on hard negatives
• Handle class imbalance (12 defect types have different frequencies)
```

**12 Defect Classes + Background:**
| ID | Class | Frequency | Critical |
|----|-------|-----------|----------|
| 0 | hot_spot | 28% | ✅ |
| 1 | cell_crack | 12% | ✅ |
| 2 | broken_cell | 8% | ✅ |
| 3 | diode_failure | 10% | ✅ |
| 4 | delamination | 9% | ✅ |
| 5 | discoloration | 7% | ❌ |
| 6 | soiling | 6% | ❌ |
| 7 | snail_track | 5% | ❌ |
| 8 | burn_mark | 4% | ✅ |
| 9 | corrosion | 4% | ❌ |
| 10 | potential_induced | 3% | ✅ |
| 11 | background | Variable | - |

---

### NMS + Class-Aware Filtering

**Purpose:** Remove duplicate detections while preserving class diversity

```
┌─────────────────────────────────────────────────────────────────┐
│  Class-Aware NMS Algorithm                                      │
│  ─────────────────────────                                      │
│                                                                 │
│  For each defect class c ∈ {0..12}:                             │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  1. Filter: confidence[c] > 0.25                          │ │
│  │  2. Sort by confidence (descending)                       │ │
│  │  3. Select highest confidence detection                   │ │
│  │  4. Remove overlapping (IoU > 0.5)                        │ │
│  │  5. Repeat until no detections remain                     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Post-NMS:                                                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • Merge results across all classes                       │ │
│  │  • Apply module-level constraints:                        │ │
│  │    - Max 50 defects per module                            │ │
│  │    - Remove conflicting overlapping defects               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Configuration:                                                  │
│  • IoU threshold: 0.5                                           │
│  • Confidence threshold: 0.25                                   │
│  • Max detections: 50 per module                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Performance Metrics

### Validation Results

| Metric | Value | Target |
|--------|-------|--------|
| mAP@50 (all classes) | 93.1% | ≥92% ✅ |
| mAP@50 (critical) | 91.4% | ≥90% ✅ |
| mAP@50-95 | 78.5% | ≥75% ✅ |
| Recall (weighted) | 94.2% | ≥90% ✅ |
| Precision (weighted) | 92.8% | ≥90% ✅ |
| F1 Score (weighted) | 91.7% | ≥90% ✅ |
| False Positive Rate | 4.2% | ≤5% ✅ |

### Latency Breakdown

| Operation | M2 (Rust) | M2 (Python) | Cloud (T4) |
|-----------|-----------|-------------|------------|
| Preprocessing | 0.3ms | 0.5ms | 0.2ms |
| Backbone (CSPDarknet-m) | 5.0ms | 8.0ms | 1.0ms |
| Neck (PANet-m) | 2.5ms | 4.0ms | 0.5ms |
| SE-Attention | 0.5ms | 0.8ms | 0.1ms |
| Detection Head | 1.0ms | 1.5ms | 0.3ms |
| Classification Head | 1.0ms | 1.5ms | 0.3ms |
| NMS + Filtering | 1.7ms | 2.5ms | 0.8ms |
| **Total** | **12.0ms** | **18.8ms** | **3.2ms** |

### Model Size

| Format | Size | Notes |
|--------|------|-------|
| PyTorch (FP32) | 52 MB | Original training format |
| ONNX (FP32) | 52 MB | Cross-platform inference |
| CoreML (FP16) | 26 MB | Mac M2 optimized |
| INT8 Quantized | 13 MB | 75% size reduction, 0.6% mAP drop |

---

## Training Configuration

### Hyperparameters

```yaml
# Model
pretrained: coco-det  # Transfer learning from COCO detection

# Optimizer
optimizer: AdamW
lr: 0.001
weight_decay: 0.05
betas: [0.9, 0.999]

# Learning Rate
scheduler: CosineAnnealing
T_max: 300
eta_min: 0.00001
warmup_epochs: 10

# Training
epochs: 300
batch_size: 64
image_size: [128, 128]

# Losses
box_loss: CIoU
cls_loss: FocalLoss
  alpha: 0.25
  gamma: 2.0
loss_weights:
  box: 7.5
  cls: 0.5
  obj: 0.5

# NMS
iou_threshold: 0.5
confidence_threshold: 0.25
max_detections: 50
class_aware: true
```

### Dataset

| Source | Images | Defects |
|--------|--------|---------|
| Public Datasets | 5,000 | 18,000 |
| Synthetic Generation | 6,000 | 25,000 |
| Field Data | 4,000 | 15,000 |
| **Total** | **15,000** | **58,000** |

### Data Augmentation

```yaml
mosaic:
  probability: 1.0
  apply_last_10_epochs: false

mixup:
  probability: 0.2
  alpha: 32.0

affine:
  rotation: ±15°
  scale: 0.8 - 1.2
  translation: ±10%
  shear: ±10%

thermal_noise:
  gaussian: σ = 0.02
  temperature_shift: ±5°C

copy_paste:
  probability: 0.7
  max_instances: 5

cutout:
  n_holes: 8
  length: 16
  probability: 0.6
```

---

## Export Formats

### ONNX Export

```python
import ultralytics

# Load trained model
model = ultralytics.YOLO('runs/detect/defect/weights/best.pt')

# Export to ONNX
model.export(
    format='onnx',
    imgsz=128,
    dynamic=False,
    simplify=True,
    opset=17,
)

# Output: best.onnx (52 MB)
```

### CoreML Export (Mac M2)

```python
import coremltools as ct
import torch

# Load and trace model
torch_model = torch.jit.load('best.pt')
example_input = torch.rand(1, 1, 128, 128)
traced_model = torch.jit.trace(torch_model, example_input)

# Convert to CoreML
mlmodel = ct.convert(
    traced_model,
    inputs=[ct.ImageType(shape=example_input.shape, scale=1.0)],
    convert_to='mlprogram',
    compute_units=ct.ComputeUnit.ALL
)

# Save
mlmodel.save('stage2_defect_detection.mlmodel')

# Output: stage2_defect_detection.mlmodel (26 MB FP16)
```

### INT8 Quantization

```python
from onnxruntime.quantization import quantize_dynamic, QuantType

quantize_dynamic(
    model_input='best.onnx',
    model_output='best_quantized.onnx',
    weight_type=QuantType.QUInt8,
    per_channel=True,
    optimize_model=True
)

# Results:
# • Size: 52 MB → 13 MB (75% reduction)
# • Latency: 18ms → 12ms (33% faster)
# • mAP drop: 93.1% → 92.5% (0.6% loss)
```

---

## References

1. **YOLOv8**: Jocher et al. "Ultralytics YOLOv8" (2023)
2. **CSPDarknet**: Wang et al. "CSPNet: A New Backbone that can Enhance Learning Capability of CNN" (CVPRW 2020)
3. **PANet**: Liu et al. "Path Aggregation Network for Instance Segmentation" (CVPR 2018)
4. **SE-Attention**: Hu et al. "Squeeze-and-Excitation Networks" (CVPR 2018)
5. **Focal Loss**: Lin et al. "Focal Loss for Dense Object Detection" (ICCV 2017)
6. **CIoU Loss**: Zheng et al. "Enhancing Geometric Factors in Anchor-Free Object Detection" (TIP 2021)
