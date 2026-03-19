# ML Pipeline - Interactive Data Flow

## Complete Pipeline Visualization

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         INPUT: Thermal Image                               │
│                                                                            │
│   Source: DJI Mavic 3T Radiometric JPEG (RJPEG)                            │
│   Resolution: 640 × 512 pixels                                             │
│   Format: 14-bit thermal data + visible light overlay                      │
│   Temperature Range: -20°C to +150°C                                       │
│   Accuracy: ±2°C or ±2% of reading                                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │                    Sample Thermal Image                          │     │
│   │                                                                  │     │
│   │    25°C  28°C  32°C  35°C  38°C  42°C  45°C  48°C  52°C  55°C   │     │
│   │    26°C  29°C  33°C  58°C  62°C  65°C  48°C  50°C  54°C  57°C   │     │
│   │    27°C  30°C  34°C  60°C  75°C  68°C  49°C  51°C  55°C  58°C   │     │
│   │    28°C  31°C  35°C  62°C  72°C  66°C  50°C  52°C  56°C  59°C   │     │
│   │    29°C  32°C  36°C  40°C  44°C  48°C  51°C  53°C  57°C  60°C   │     │
│   │                                                                  │     │
│   │    [████████] Hotspot detected at cells [12,13,22,23]            │     │
│   │    Max Temp: 75.5°C  │  Ambient: 35.0°C  │  ΔT: 40.5°C           │     │
│   └─────────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: Hotspot Detector                                                 │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                            │
│  Architecture: MobileNetV3-Small (Binary Classification)                   │
│  Model Size: 2.1 MB  │  FLOPs: 45M  │  Latency: 2.5ms (edge)              │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │  Model Architecture:                                              │     │
│  │                                                                   │     │
│  │  Input [640×512×1]                                                │     │
│  │       │                                                           │     │
│  │       ▼                                                           │     │
│  │  ┌─────────────────────────────────────────┐                     │     │
│  │  │ Conv2D(32, 3×3, s=2) → BN → ReLU        │ [320×256×32]        │     │
│  │  └─────────────────────────────────────────┘                     │     │
│  │       │                                                           │     │
│  │       ▼                                                           │     │
│  │  ┌─────────────────────────────────────────┐                     │     │
│  │  │ Conv2D(64, 3×3, s=2) → BN → ReLU        │ [160×128×64]        │     │
│  │  └─────────────────────────────────────────┘                     │     │
│  │       │                                                           │     │
│  │       ▼                                                           │     │
│  │  ┌─────────────────────────────────────────┐                     │     │
│  │  │ Conv2D(128, 3×3, s=2) → BN → ReLU       │ [80×64×128]         │     │
│  │  └─────────────────────────────────────────┘                     │     │
│  │       │                                                           │     │
│  │       ▼                                                           │     │
│  │  ┌─────────────────────────────────────────┐                     │     │
│  │  │ Global Average Pooling                  │ [1×1×128]           │     │
│  │  └─────────────────────────────────────────┘                     │     │
│  │       │                                                           │     │
│  │       ▼                                                           │     │
│  │  ┌─────────────────────────────────────────┐                     │     │
│  │  │ Dense(128) → ReLU → Dropout(0.3)        │ [128]               │     │
│  │  └─────────────────────────────────────────┘                     │     │
│  │       │                                                           │     │
│  │       ▼                                                           │     │
│  │  ┌─────────────────────────────────────────┐                     │     │
│  │  │ Dense(1) → Sigmoid                      │ [1]                 │     │
│  │  └─────────────────────────────────────────┘                     │     │
│  │                                                                   │     │
│  │  Output: hotspot_probability = 0.89                               │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  Decision: confidence (0.89) > threshold (0.65) = ✓ PASS to Stage 2       │
│                                                                            │
│  Output JSON:                                                              │
│  {                                                                         │
│    "stage": 1,                                                             │
│    "hotspot_detected": true,                                               │
│    "confidence": 0.89,                                                     │
│    "processing_time_ms": 2.5,                                              │
│    "passed_to_stage_2": true                                               │
│  }                                                                         │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: Cell Analyzer                                                    │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                            │
│  Architecture: UNet-ResNet34 (Semantic Segmentation + Feature Extraction) │
│  Model Size: 18.5 MB  │  FLOPs: 380M  │  Latency: 8.0ms (edge)            │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │  Cell Layout (6 rows × 10 columns = 60 cells):                   │     │
│  │                                                                   │     │
│  │  ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐                                │     │
│  │  │ 0│ 1│ 2│ 3│ 4│ 5│ 6│ 7│ 8│ 9│                                │     │
│  │  ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤                                │     │
│  │  │10│11│12│13│14│15│16│17│18│19│  ← Affected cells highlighted  │     │
│  │  ├──┼──┼██│██┼──┼──┼──┼──┼──┼──┤                                │     │
│  │  │20│21│22│23│24│25│26│27│28│29│  [12, 13, 22, 23]              │     │
│  │  ├──┼──┼██│██┼──┼──┼──┼──┼──┼──┤                                │     │
│  │  │30│31│32│33│34│35│36│37│38│39│                                │     │
│  │  ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤                                │     │
│  │  │40│41│42│43│44│45│46│47│48│49│                                │     │
│  │  └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘                                │     │
│  │                                                                   │     │
│  │  Affected Cell Features:                                          │     │
│  │  ┌────────────────────────────────────────────────────────────┐  │     │
│  │  │ Cell 12: ΔT=15.2°C, Area=245px, Pos=[2,2], Feat=[0.82...]  │  │     │
│  │  │ Cell 13: ΔT=14.8°C, Area=238px, Pos=[2,3], Feat=[0.79...]  │  │     │
│  │  │ Cell 22: ΔT=8.5°C,  Area=156px, Pos=[3,2], Feat=[0.65...]  │  │     │
│  │  │ Cell 23: ΔT=9.1°C,  Area=162px, Pos=[3,3], Feat=[0.68...]  │  │     │
│  │  └────────────────────────────────────────────────────────────┘  │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  Output JSON:                                                              │
│  {                                                                         │
│    "stage": 2,                                                             │
│    "affected_cells": [12, 13, 22, 23],                                     │
│    "cell_anomaly_map": "base64_encoded_segmentation_mask",                 │
│    "cell_features": {                                                      │
│      "12": {"temp_delta": 15.2, "area_pixels": 245, "position": [2, 2]},   │
│      "13": {"temp_delta": 14.8, "area_pixels": 238, "position": [2, 3]},   │
│      "22": {"temp_delta": 8.5,  "area_pixels": 156, "position": [3, 2]},   │
│      "23": {"temp_delta": 9.1,  "area_pixels": 162, "position": [3, 3]}    │
│    },                                                                      │
│    "processing_time_ms": 8.0                                               │
│  }                                                                         │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: Module Classifier                                                │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                            │
│  Architecture: ResNet-18 + Transformer Encoder (8-class Classification)   │
│  Model Size: 45.2 MB  │  FLOPs: 890M  │  Latency: 12.0ms (edge)           │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │  Defect Type Classification Results:                              │     │
│  │                                                                   │     │
│  │  ┌────────────────────────────────────────────────────────────┐  │     │
│  │  │ 0.91 │████████████████████████████████████████████████│    │  │     │
│  │  │      │ hotspot                                         │    │  │     │
│  │  ├────────────────────────────────────────────────────────────┤  │     │
│  │  │ 0.05 │█████                                               │    │  │     │
│  │  │      │ cell_anomaly                                      │    │  │     │
│  │  ├────────────────────────────────────────────────────────────┤  │     │
│  │  │ 0.02 │██                                                  │    │  │     │
│  │  │      │ delamination                                      │    │  │     │
│  │  ├────────────────────────────────────────────────────────────┤  │     │
│  │  │ 0.01 │█                                                   │    │  │     │
│  │  │      │ diode_failure                                     │    │  │     │
│  │  ├────────────────────────────────────────────────────────────┤  │     │
│  │  │ 0.005│                                                    │    │  │     │
│  │  │      │ crack                                             │    │  │     │
│  │  ├────────────────────────────────────────────────────────────┤  │     │
│  │  │ 0.003│                                                    │    │  │     │
│  │  │      │ soiling                                           │    │  │     │
│  │  ├────────────────────────────────────────────────────────────┤  │     │
│  │  │ 0.002│                                                    │    │  │     │
│  │  │      │ discoloration                                     │    │  │     │
│  │  ├────────────────────────────────────────────────────────────┤  │     │
│  │  │ 0.000│                                                    │    │  │     │
│  │  │      │ normal                                            │    │  │     │
│  │  └────────────────────────────────────────────────────────────┘  │     │
│  │                                                                   │     │
│  │  Predicted: HOTSPOT (confidence: 91%)                             │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  Output JSON:                                                              │
│  {                                                                         │
│    "stage": 3,                                                             │
│    "defect_type": "hotspot",                                               │
│    "defect_type_id": 0,                                                    │
│    "confidence": 0.91,                                                     │
│    "all_probabilities": {                                                  │
│      "hotspot": 0.91, "cell_anomaly": 0.05, "delamination": 0.02,          │
│      "diode_failure": 0.01, "crack": 0.005, "soiling": 0.003,              │
│      "discoloration": 0.002, "normal": 0.0                                 │
│    },                                                                      │
│    "processing_time_ms": 12.0                                              │
│  }                                                                         │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: Severity Scorer                                                  │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                            │
│  Architecture: Multi-Branch Network (Severity + Confidence + Recs)        │
│  Model Size: 8.5 MB  │  FLOPs: 120M  │  Latency: 5.0ms (edge)             │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │  Severity Calculation:                                            │     │
│  │                                                                   │     │
│  │  Inputs:                                                          │     │
│  │  ├─ Temperature Delta: 40.5°C                                     │     │
│  │  ├─ Affected Cells: 4/60 (6.7%)                                   │     │
│  │  ├─ Defect Type: hotspot                                          │     │
│  │  └─ Module Specs: rated_power=400W, temp_coeff=-0.0035            │     │
│  │                                                                   │     │
│  │  Severity Score Calculation:                                      │     │
│  │  ┌────────────────────────────────────────────────────────────┐  │     │
│  │  │ severity = min(1.0, temp_delta / 45.0)                     │  │     │
│  │  │          = min(1.0, 40.5 / 45.0)                           │  │     │
│  │  │          = 0.90 → CRITICAL                                 │  │     │
│  │  └────────────────────────────────────────────────────────────┘  │     │
│  │                                                                   │     │
│  │  Severity Scale:                                                  │     │
│  │  ┌────────────────────────────────────────────────────────────┐  │     │
│  │  │ LOW      [████░░░░░░░░░░░░░░░░░░░] 0.00 - 0.25             │  │     │
│  │  │ MEDIUM   [░░░░████░░░░░░░░░░░░░░░] 0.25 - 0.50             │  │     │
│  │  │ HIGH     [░░░░░░░░████░░░░░░░░░░░] 0.50 - 0.75             │  │     │
│  │  │ CRITICAL [░░░░░░░░░░░░████████████] 0.75 - 1.00 ← HERE     │  │     │
│  │  └────────────────────────────────────────────────────────────┘  │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  Output JSON:                                                              │
│  {                                                                         │
│    "stage": 4,                                                             │
│    "severity": {                                                           │
│      "score": 0.90,                                                        │
│      "level": "critical",                                                  │
│      "normalized_temperature_delta": 0.90                                  │
│    },                                                                      │
│    "confidence": {                                                         │
│      "score": 0.94,                                                        │
│      "uncertainty": 0.06,                                                  │
│      "calibration_method": "temperature_scaling"                           │
│    },                                                                      │
│    "recommendations": [                                                    │
│      {                                                                     │
│        "priority": 1,                                                      │
│        "action": "IMMEDIATE_REPLACEMENT",                                  │
│        "description": "Module shows critical hotspot with 40.5°C ΔT",      │
│        "estimated_power_loss": "15-20%",                                   │
│        "safety_risk": "Fire hazard - thermal runaway possible"             │
│      },                                                                    │
│      {                                                                     │
│        "priority": 2,                                                      │
│        "action": "INSPECT_ADJACENT_MODULES",                               │
│        "description": "Check modules in same substring for cascading"      │
│      },                                                                    │
│      {                                                                     │
│        "priority": 3,                                                      │
│        "action": "CHECK_CONNECTIONS",                                      │
│        "description": "Verify MC4 connectors and wiring integrity"         │
│      }                                                                     │
│    ],                                                                      │
│    "processing_time_ms": 5.0                                               │
│  }                                                                         │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         FINAL OUTPUT                                       │
│                                                                            │
│  {                                                                         │
│    "module_id": "mod_001_05",                                              │
│    "inspection_id": "insp_001",                                            │
│    "image_id": "img_insp_001_mod_005",                                     │
│    "defect_type": "hotspot",                                               │
│    "severity": "critical",                                                 │
│    "severity_score": 0.90,                                                 │
│    "confidence": 0.94,                                                     │
│    "temperature_delta": 40.5,                                              │
│    "max_temperature": 75.5,                                                │
│    "ambient_temperature": 35.0,                                            │
│    "affected_cells": [12, 13, 22, 23],                                     │
│    "recommendations": [ /* ... */ ],                                       │
│    "stage_times": {                                                        │
│      "stage1": 2.5,                                                        │
│      "stage2": 8.0,                                                        │
│      "stage3": 12.0,                                                       │
│      "stage4": 5.0                                                         │
│    },                                                                      │
│    "total_processing_time_ms": 27.5,                                       │
│    "model_version": "1.0.0",                                               │
│    "device": "edge"                                                        │
│  }                                                                         │
│                                                                            │
│  Performance Summary:                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │  ✓ Total Latency: 27.5ms (edge) / 8.8ms (cloud GPU)             │      │
│  │  ✓ Model Size: 74.3 MB total                                    │      │
│  │  ✓ Throughput: 36 images/sec (edge) / 114 images/sec (cloud)    │      │
│  │  ✓ Accuracy: 91% overall classification                         │      │
│  └─────────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Early Exit Optimization

The pipeline supports **early exit** at multiple stages to optimize latency:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Early Exit Decision Points                    │
└─────────────────────────────────────────────────────────────────┘

Stage 1 Exit (No Hotspot):
├─ Condition: hotspot_probability < 0.65
├─ Latency: 2.5ms (91% reduction)
└─ Output: "normal" - no further processing

Stage 2 Exit (Low Confidence):
├─ Condition: cell_analysis_confidence < 0.50
├─ Latency: 10.5ms
└─ Output: "manual_review" - flag for human inspection

Stage 3 Exit (Normal Classification):
├─ Condition: defect_type == "normal" AND confidence > 0.95
├─ Latency: 22.5ms
└─ Output: "normal" - skip severity scoring

Full Pipeline:
├─ All stages complete
├─ Latency: 27.5ms
└─ Output: Complete defect analysis with recommendations
```

---

## Batch Processing Mode

For processing multiple modules simultaneously:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Batch Processing (8 images)                   │
└─────────────────────────────────────────────────────────────────┘

Input: [img_001, img_002, img_003, img_004, img_005, img_006, img_007, img_008]
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Batch Inference (8 images simultaneously)              │
│  Input:  [8, 1, 640, 512]                                        │
│  Output: [8] hotspot probabilities                               │
│  Time: 3.0ms (vs 20ms sequential)                                │
│  Results: [✓, ✗, ✓, ✓, ✗, ✓, ✗, ✓]  → 5 pass to Stage 2         │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: Batch Inference (5 remaining images)                   │
│  Input:  [5, 1, 640, 512]                                        │
│  Output: [5] cell feature sets                                   │
│  Time: 9.0ms (vs 40ms sequential)                                │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: Batch Inference (5 images)                             │
│  Input:  [5, 512]  (feature vectors)                             │
│  Output: [5] defect classifications                              │
│  Time: 13.0ms (vs 60ms sequential)                               │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 4: Batch Inference (5 images)                             │
│  Input:  [5, 512]  (concatenated features)                       │
│  Output: [5] severity scores + recommendations                   │
│  Time: 6.0ms (vs 25ms sequential)                                │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
Total Batch Time: 31ms (vs 145ms sequential) = 78% reduction
```

---

## Model Ensemble (Optional)

For critical applications requiring higher accuracy:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ensemble Mode (3 models)                      │
└─────────────────────────────────────────────────────────────────┘

Stage 3 Ensemble:
┌──────────────────┐
│  Model A (Main)  │ → [0.91, 0.05, 0.02, ...]
│  ResNet18+Trans  │
└──────────────────┘
┌──────────────────┐
│  Model B (Large) │ → [0.88, 0.07, 0.03, ...]
│  EfficientNet-B3 │
└──────────────────┘
┌──────────────────┐
│  Model C (Fast)  │ → [0.85, 0.08, 0.04, ...]
│  MobileNetV3     │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  Weighted Average│ → [0.89, 0.06, 0.03, ...]
│  (weights: 0.5,  │
│   0.3, 0.2)      │
└──────────────────┘
       │
       ▼
Final: HOTSPOT (confidence: 0.89)

Ensemble Benefits:
├─ Accuracy: 91% → 94%
├─ Robustness: Better handling of edge cases
└─ Cost: 3x latency, 3x model size
```
