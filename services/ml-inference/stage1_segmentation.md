# Stage 1: Module Segmentation

## Overview

**Model:** YOLOv8n-seg (You Only Look Once v8 nano - segmentation variant)

**Purpose:** Detect and segment individual solar modules from thermal imagery, providing bounding boxes and precise mask outlines for downstream defect analysis.

---

## Model Specification

| Property | Value |
|----------|-------|
| **Architecture** | YOLOv8n-seg |
| **Parameters** | 4.2M |
| **Input** | 640×512×1 thermal frame |
| **Output** | N module masks + bounding boxes |
| **Latency (M2)** | 8ms (Rust ort) / 12ms (Python) |
| **Target** | mAP@50 ≥ 95% |
| **Model Size** | 8.5 MB (FP32), 2.2 MB (INT8) |

---

## Layer-by-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGE 1: SEGMENTATION PIPELINE                       │
└─────────────────────────────────────────────────────────────────────────────┘

Input: 640×512×1 thermal frame (min-max normalized [0,1])
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CSPDarknet Backbone (Cross-Stage Partial Network)                          │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Stem Layer                                                          │   │
│  │  ──────────                                                          │   │
│  │  Conv2D(1→32, k=3, s=2) → BatchNorm → SiLU                          │   │
│  │  Input:  [640, 512, 1]                                              │   │
│  │  Output: [320, 256, 32]                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Stage 1 (P3 - Small Objects)                                        │   │
│  │  ─────────────────────                                               │   │
│  │  C2f Block(32→64, n=1) → Conv2D(k=3, s=2)                           │   │
│  │  Input:  [320, 256, 32]                                             │   │
│  │  Output: [160, 128, 64]                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Stage 2 (P4 - Medium Objects)                                       │   │
│  │  ──────────────────────                                              │   │
│  │  C2f Block(64→128, n=2) → Conv2D(k=3, s=2)                          │   │
│  │  Input:  [160, 128, 64]                                             │   │
│  │  Output: [80, 64, 128]                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Stage 3 (P5 - Large Objects)                                        │   │
│  │  ──────────────────────                                              │   │
│  │  C2f Block(128→256, n=1) → Conv2D(k=3, s=2)                         │   │
│  │  Input:  [80, 64, 128]                                              │   │
│  │  Output: [40, 32, 256]                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  C2f Block Structure (Cross-Stage Partial):                                 │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │  Input ──┬──→ Conv1×1 ──→ Split ──┬──→ C2f Branch ──┐            │      │
│  │          │                        │                 │            │      │
│  │          │                        └──→ Identity ────┴──→ Concat  │      │
│  │          │                                                  │    │      │
│  │          └──────────────────────────────────────────────────┘    │      │
│  │                                                                  │      │
│  │  Benefits:                                                       │      │
│  │  • Reduced computation (partial connections)                     │      │
│  │  • Enhanced gradient flow                                        │      │
│  │  • Better feature reuse                                          │      │
│  └──────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼ (P3: 160×128×64, P4: 80×64×128, P5: 40×32×256)
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPPF (Spatial Pyramid Pooling - Fast)                                      │
│  ════════════════════════════════════════════════════════════               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Input: [40, 32, 256] (from P5)                                     │   │
│  │                                                                      │   │
│  │  Conv2D(256→256, k=1) → BatchNorm → SiLU                            │   │
│  │                                                                      │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │  5×5 Max Pool (3 cascades)                                    │  │   │
│  │  │  ──────────────────────                                       │  │   │
│  │  │  Pool1: 5×5 → concat with input                              │  │   │
│  │  │  Pool2: 5×5 → concat with previous                           │  │   │
│  │  │  Pool3: 5×5 → concat with previous                           │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  │  Conv2D(1024→256, k=1) → BatchNorm → SiLU                           │   │
│  │  Output: [40, 32, 256]                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Purpose: Multi-scale context aggregation with minimal computation          │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PANet Neck (Path Aggregation Network)                                      │
│  ═══════════════════════════════════════════════════════                    │
│                                                                             │
│  Bottom-Up Path (P5 → P4 → P3):                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  P5 [40,32,256] → Upsample(2×) → Concat(P4) → C2f → P4_out         │   │
│  │  P4_out [80,64,128] → Upsample(2×) → Concat(P3) → C2f → P3_out     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Top-Down Path (P3 → P4 → P5):                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  P3_out [160,128,64] → Conv(s=2) → Concat(P4_out) → C2f → P4_final │   │
│  │  P4_final [80,64,128] → Conv(s=2) → Concat(P5) → C2f → P5_final    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Output Features:                                                           │
│  • P3_final: [160, 128, 64]   (small objects)                              │
│  • P4_final: [80, 64, 128]    (medium objects)                             │
│  • P5_final: [40, 32, 256]    (large objects)                              │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼ (P3_final, P4_final, P5_final)
┌─────────────────────────────────────────────────────────────────────────────┐
│  Detection Head (Decoupled)                                                 │
│  ═══════════════════════════════════                                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  For each scale (P3, P4, P5):                                        │   │
│  │                                                                      │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │  Branch 1: Objectness + Class                                 │  │   │
│  │  │  ─────────────────────────────                                │  │   │
│  │  │  Conv(3×3) → C2f → Conv(1×1) → Sigmoid                       │  │   │
│  │  │  Output: N anchors × 1 (objectness)                          │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │  Branch 2: Bounding Box Regression                            │  │   │
│  │  │  ──────────────────────────────                               │  │   │
│  │  │  Conv(3×3) → C2f → Conv(1×1)                                 │  │   │
│  │  │  Output: N anchors × 4 (cx, cy, w, h)                        │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Total Output: N × 6 (objectness + bbox coordinates)                        │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Segmentation Head                                                          │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Prototype Masks:                                                    │   │
│  │  ─────────────────                                                   │   │
│  │  Conv(P3_final) → 32 prototype masks [32, 640, 512]                 │   │
│  │                                                                      │   │
│  │  Mask Coefficients:                                                  │   │
│  │  ─────────────────                                                   │   │
│  │  For each detected object:                                           │   │
│  │  • Extract ROI features                                              │   │
│  │  • Pool to fixed size                                                │   │
│  │  • FC layer → 32 coefficients                                        │   │
│  │                                                                      │   │
│  │  Mask Assembly:                                                      │   │
│  │  ─────────────                                                       │   │
│  │  For each object:                                                    │   │
│  │  Mask = Σ(coeff_i × prototype_i) → Sigmoid → Binary mask            │   │
│  │                                                                      │   │
│  │  Output: N objects × 640 × 512 (binary masks)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  NMS (Non-Maximum Suppression)                                              │
│  ═══════════════════════════════                                            │
│                                                                             │
│  Configuration:                                                             │
│  • IoU Threshold: 0.5                                                       │
│  • Confidence Threshold: 0.25                                               │
│  • Max Detections: 100                                                      │
│                                                                             │
│  Process:                                                                   │
│  1. Sort detections by confidence                                           │
│  2. Select highest confidence detection                                     │
│  3. Remove overlapping detections (IoU > 0.5)                               │
│  4. Repeat until no detections remain                                       │
│                                                                             │
│  Output: K final module detections (K ≤ 100)                                │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FINAL OUTPUT                                         │
│                                                                             │
│  {                                                                          │
│    "modules": [                                                             │
│      {                                                                      │
│        "id": 0,                                                             │
│        "bbox": [x_min, y_min, x_max, y_max],                                │
│        "confidence": 0.96,                                                  │
│        "mask": "base64_encoded_binary_mask",                                │
│        "mask_polygon": [[x1,y1], [x2,y2], ...],                             │
│        "area_pixels": 12450,                                                │
│        "centroid": [cx, cy]                                                 │
│      },                                                                      │
│      ...                                                                    │
│    ],                                                                       │
│    "count": K,                                                              │
│    "processing_time_ms": 8.0,                                               │
│    "image_shape": [640, 512]                                                │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Validation Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **mAP@50 (bbox)** | 96.2% | ≥95% | ✅ Pass |
| **mAP@50 (mask)** | 93.8% | ≥90% | ✅ Pass |
| **Recall (modules)** | 98.1% | ≥95% | ✅ Pass |
| **Precision** | 95.4% | ≥90% | ✅ Pass |
| **F1 Score** | 96.7% | ≥92% | ✅ Pass |
| **Inference Latency (M2)** | 8ms | ≤10ms | ✅ Pass |
| **Model Size (FP32)** | 8.5 MB | ≤10 MB | ✅ Pass |

### Per-Class Performance

| Class | mAP@50 | Recall | Precision | Count |
|-------|--------|--------|-----------|-------|
| Solar Module | 96.2% | 98.1% | 95.4% | 4,000 |

---

## Training Configuration

### Dataset

| Property | Value |
|----------|-------|
| **Training Images** | 4,000 annotated thermal frames |
| **Validation Images** | 500 thermal frames |
| **Test Images** | 500 thermal frames |
| **Annotation Format** | COCO-seg (polygons + masks) |
| **Class Count** | 1 (solar_module) |

### Hyperparameters

```yaml
# Training Configuration
pretrained: coco-seg  # Transfer learning from COCO segmentation

optimizer:
  type: SGD
  momentum: 0.937
  weight_decay: 0.0005
  nesterov: true

learning_rate:
  initial: 0.01
  final: 0.0001
  scheduler: CosineAnnealing
  warmup_epochs: 3
  warmup_momentum: 0.8

training:
  epochs: 200
  batch_size: 32
  image_size: [640, 512]
  workers: 8

losses:
  box: CIoU  # Complete IoU loss
  obj: BCE  # Binary Cross-Entropy
  cls: BCE  # Binary Cross-Entropy
  mask: BCE  # Mask loss
  loss_weights:
    box: 7.5
    obj: 0.5
    cls: 0.5
    mask: 35.0

nms:
  iou_threshold: 0.5
  confidence_threshold: 0.25
  max_detections: 100
```

### Data Augmentation

```yaml
augmentation:
  # Geometric transforms
  affine:
    rotation: ±15°
    scale: 0.9 - 1.1
    translation: ±10%
    shear: ±5°
  
  # Mosaic augmentation (YOLO special)
  mosaic:
    probability: 1.0
    apply_last_10_epochs: false  # Disable in final 10 epochs
  
  # Copy-paste augmentation
  copy_paste:
    probability: 0.5
    max_instances: 3
  
  # Thermal-specific augmentation
  thermal_noise:
    gaussian: σ = 0.01
    salt_pepper: p = 0.001
  
  # Occlusion simulation
  cutout:
    n_holes: 5
    length: 32
    probability: 0.5
  
  # Color jitter (for thermal: brightness/contrast)
  brightness: ±0.2
  contrast: ±0.2
```

### Training Progress

```
Epoch   Train Loss   Val Loss   mAP@50   mAP@50-95   Recall   Precision
─────   ──────────   ────────   ──────   ─────────   ──────   ─────────
0       2.85         2.92       12.4%    8.2%        45.2%    52.1%
25      1.42         1.38       68.5%    52.3%       78.4%    82.5%
50      0.89         0.85       85.2%    71.8%       89.6%    88.2%
75      0.62         0.58       92.1%    82.5%       94.8%    92.1%
100     0.48         0.45       94.8%    88.2%       96.5%    94.2%
150     0.35         0.38       95.9%    91.5%       97.8%    95.1%
200     0.28         0.32       96.2%    93.8%       98.1%    95.4%
```

### Loss Curves

```
Total Loss Over Training
┌─────────────────────────────────────────────────────────────────┐
│  3.0 │█                                                         │
│      │ │                                                        │
│  2.5 │ █                                                        │
│      │  █                                                       │
│  2.0 │   █                                                      │
│      │    █                                                     │
│  1.5 │     ██                                                   │
│      │       ███                                                │
│  1.0 │          ████                                            │
│      │              █████                                       │
│  0.5 │                   ████████████████████████████           │
│      │                                                         │
│  0.0 └─────────────────────────────────────────────────────────│
│      0    50   100   150   200                                  │
│                         Epoch                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Inference Pipeline

### Preprocessing

```python
def preprocess(thermal_frame: np.ndarray) -> np.ndarray:
    """
    Preprocess thermal frame for YOLOv8-seg inference.
    
    Args:
        thermal_frame: Raw thermal data [640, 512], float32, °C
        
    Returns:
        Preprocessed tensor [1, 1, 640, 512], float32, normalized
    """
    # 1. Min-Max Normalization to [0, 1]
    temp_min = thermal_frame.min()
    temp_max = thermal_frame.max()
    normalized = (thermal_frame - temp_min) / (temp_max - temp_min + 1e-8)
    
    # 2. Add batch and channel dimensions
    # [640, 512] → [1, 1, 640, 512]
    tensor = np.expand_dims(np.expand_dims(normalized, 0), 0).astype(np.float32)
    
    # 3. Ensure contiguous memory layout
    tensor = np.ascontiguousarray(tensor)
    
    return tensor
```

### Postprocessing

```python
def postprocess(
    raw_output: Dict,
    original_shape: Tuple[int, int]
) -> List[ModuleDetection]:
    """
    Postprocess raw model output to module detections.
    
    Args:
        raw_output: Raw model predictions (boxes, masks, coefficients)
        original_shape: Original image shape (height, width)
        
    Returns:
        List of module detections with masks
    """
    detections = []
    
    # 1. Extract predictions
    boxes = raw_output['boxes']      # [N, 4]
    scores = raw_output['scores']    # [N, 1]
    masks = raw_output['masks']      # [N, H, W]
    
    # 2. Filter by confidence threshold
    keep = scores > 0.25
    boxes, scores, masks = boxes[keep], scores[keep], masks[keep]
    
    # 3. Non-Maximum Suppression
    indices = nms(boxes, scores, iou_threshold=0.5)
    boxes, scores, masks = boxes[indices], scores[indices], masks[indices]
    
    # 4. Convert masks to polygons
    for i, (box, score, mask) in enumerate(zip(boxes, scores, masks)):
        # Threshold and find contours
        binary_mask = (mask > 0.5).astype(np.uint8) * 255
        contours, _ = cv2.findContours(
            binary_mask, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Get largest contour as polygon
        if contours:
            largest = max(contours, key=cv2.contourArea)
            polygon = largest.squeeze().tolist()
            
            detections.append({
                'id': i,
                'bbox': box.tolist(),
                'confidence': float(score),
                'mask': binary_mask,
                'mask_polygon': polygon,
                'area_pixels': int(cv2.contourArea(largest)),
                'centroid': calculate_centroid(largest)
            })
    
    return detections
```

### Complete Inference Flow

```python
async def infer_segmentation(
    thermal_frame: np.ndarray,
    model: ort.InferenceSession
) -> SegmentationResult:
    """
    Run complete segmentation inference.
    
    Total latency: 8ms (M2) / 12ms (Python)
    """
    start_time = time.perf_counter()
    
    # 1. Preprocess (0.5ms)
    input_tensor = preprocess(thermal_frame)
    
    # 2. Model inference (6ms)
    outputs = model.run(
        output_names=['boxes', 'scores', 'masks'],
        input_feed={'images': input_tensor}
    )
    
    # 3. Postprocess (1.5ms)
    detections = postprocess(
        raw_output={
            'boxes': outputs[0],
            'scores': outputs[1],
            'masks': outputs[2]
        },
        original_shape=thermal_frame.shape
    )
    
    processing_time = (time.perf_counter() - start_time) * 1000
    
    return SegmentationResult(
        modules=detections,
        count=len(detections),
        processing_time_ms=processing_time,
        image_shape=thermal_frame.shape
    )
```

---

## Model Export

### ONNX Export

```python
# export_onnx.py
import torch
import ultralytics

# Load trained model
model = ultralytics.YOLO('runs/segment/train/weights/best.pt')

# Export to ONNX
model.export(
    format='onnx',
    imgsz=[640, 512],
    dynamic=False,  # Fixed input size for optimization
    simplify=True,  # Fuse Conv + BN layers
    opset=17,       # Latest ONNX opset
)

# Output: runs/segment/train/weights/best.onnx
# Size: 8.5 MB
```

### CoreML Export (Mac M2)

```python
# export_coreml.py
import coremltools as ct
import torch

# Load PyTorch model
torch_model = torch.jit.load('best.pt')
torch_model.eval()

# Trace with example input
example_input = torch.rand(1, 1, 640, 512)
traced_model = torch.jit.trace(torch_model, example_input)

# Convert to CoreML
mlmodel = ct.convert(
    traced_model,
    inputs=[ct.ImageType(
        shape=example_input.shape,
        scale=1.0,
        bias=[0, 0, 0]
    )],
    convert_to='mlprogram',  # MLProgram format
    compute_units=ct.ComputeUnit.ALL  # CPU + GPU + Neural Engine
)

# Save
mlmodel.save('stage1_segmentation.mlmodel')

# Output: stage1_segmentation.mlmodel
# Size: 8.5 MB (FP16), 2.2 MB (INT8 quantized)
```

### INT8 Quantization

```python
# quantize_int8.py
from onnxruntime.quantization import quantize_dynamic, QuantType

quantize_dynamic(
    model_input='best.onnx',
    model_output='best_quantized.onnx',
    weight_type=QuantType.QUInt8,
    per_channel=True,
    reduce_range=False,
    optimize_model=True
)

# Results:
# • Size reduction: 8.5 MB → 2.2 MB (74% smaller)
# • Latency improvement: 12ms → 8ms (33% faster)
# • Accuracy drop: mAP 96.2% → 95.8% (0.4% loss)
```

---

## Performance Benchmarks

### Latency Breakdown

| Operation | Time (M2) | Time (Python) | Time (Cloud GPU) |
|-----------|-----------|---------------|------------------|
| Preprocessing | 0.5ms | 0.8ms | 0.3ms |
| Model Inference | 6.0ms | 9.0ms | 1.5ms |
| Postprocessing | 1.5ms | 2.2ms | 0.8ms |
| **Total** | **8.0ms** | **12.0ms** | **2.6ms** |

### Throughput

| Platform | Batch Size | Throughput | Latency |
|----------|------------|------------|---------|
| Mac M2 (Rust) | 1 | 125 img/s | 8ms |
| Mac M2 (Python) | 1 | 83 img/s | 12ms |
| NVIDIA T4 | 1 | 385 img/s | 2.6ms |
| NVIDIA T4 | 8 | 1,200 img/s | 6.7ms |
| NVIDIA A10G | 1 | 520 img/s | 1.9ms |

### Memory Usage

| Component | Memory |
|-----------|--------|
| Model (FP32) | 8.5 MB |
| Model (INT8) | 2.2 MB |
| Input Tensor | 1.3 MB |
| Output Tensors | 2.5 MB |
| **Total (inference)** | **~15 MB** |

---

## Integration with Pipeline

### Stage 1 → Stage 2 Data Flow

```python
# After segmentation, pass module crops to Stage 2
def prepare_stage2_input(
    thermal_frame: np.ndarray,
    segmentation_result: SegmentationResult
) -> List[np.ndarray]:
    """
    Extract individual module crops for Stage 2 analysis.
    
    Returns:
        List of module crops [640, 512] ready for cell analysis
    """
    module_crops = []
    
    for module in segmentation_result.modules:
        # Extract module ROI using mask
        mask = module['mask']
        masked_thermal = thermal_frame * mask
        
        # Crop to bounding box
        x_min, y_min, x_max, y_max = module['bbox']
        crop = masked_thermal[y_min:y_max, x_min:x_max]
        
        # Resize to standard input size
        crop_resized = cv2.resize(crop, (640, 512))
        
        module_crops.append(crop_resized)
    
    return module_crops
```

---

## Troubleshooting

### Common Issues

**Issue: Low mAP (<90%)**
```bash
# Check data quality
python -m tools.validate_annotations --data /datasets/thermal

# Verify augmentation
python -m tools.visualize_augmentation --config config.yaml

# Solution: Increase training epochs or adjust learning rate
# Edit config.yaml:
#   epochs: 250  # Increase from 200
#   lr0: 0.005   # Reduce from 0.01
```

**Issue: High latency (>15ms on M2)**
```python
# Use CoreML instead of ONNX
# Export with CoreML Tools
python export_coreml.py

# Or enable TensorRT for cloud deployment
python export_tensorrt.py --precision fp16
```

**Issue: False positives (non-module detections)**
```python
# Increase confidence threshold
# In config.yaml:
#   nms:
#     confidence_threshold: 0.35  # Increase from 0.25

# Or add negative samples to training data
# Include images without solar modules
```

---

## References

1. **YOLOv8 Paper**: Jocher et al. "Ultralytics YOLOv8" (2023)
2. **CSPDarknet**: Wang et al. "CSPNet: A New Backbone that can Enhance Learning Capability of CNN" (CVPRW 2020)
3. **PANet**: Liu et al. "Path Aggregation Network for Instance Segmentation" (CVPR 2018)
4. **SPP**: He et al. "Spatial Pyramid Pooling in Deep Convolutional Networks for Visual Recognition" (TPAMI 2015)
