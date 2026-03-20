# Google Colab Training Guide - Stage 1

## Quick Start

### 1. Open Colab Notebook

**Option A: Use the provided notebook**
1. Open: `Doctor_Doom_ML_Training_Colab.ipynb`
2. Click "Open in Colab" or upload to your Google Drive

**Option B: Create new notebook**
1. Go to https://colab.research.google.com
2. Click "New Notebook"
3. Copy code from sections below

---

## Step-by-Step Instructions

### Step 1: Setup Colab Environment

```python
# Check GPU availability
!nvidia-smi

# Mount Google Drive (optional, for saving models)
from google.colab import drive
drive.mount('/content/drive')

# Install dependencies
!pip install ultralytics roboflow

# Verify installation
import ultralytics
print(f"Ultralytics version: {ultralytics.__version__}")
```

### Step 2: Upload Dataset

**Method A: Direct Upload (for small datasets)**

```python
from google.colab import files
uploaded = files.upload()  # Upload dataset_1.zip
!unzip -q dataset_1.zip
```

**Method B: Google Drive**

```python
# Copy from Google Drive
!cp /content/drive/MyDrive/dataset_1.zip .
!unzip -q dataset_1.zip
```

**Method C: Download from URL**

```python
# If dataset is hosted somewhere
!wget https://your-url.com/dataset_1.zip
!unzip -q dataset_1.zip
```

### Step 3: Prepare Dataset

```python
# Run the preparation script
!python scripts/prepare_dataset_stage1.py \
    --dataset dataset_1 \
    --output datasets/processed/stage1 \
    --val-split 0.2
```

### Step 4: Train Model

```python
# Train on Colab GPU (FREE T4)
!python scripts/train_stage1.py \
    --data datasets/processed/stage1/data.yaml \
    --epochs 100 \
    --batch-size 32 \
    --device 0 \
    --name stage1_colab \
    --project /content/drive/MyDrive/doctor-doom/models

# Or train on Colab Pro (A100/V100)
!python scripts/train_stage1.py \
    --data datasets/processed/stage1/data.yaml \
    --epochs 200 \
    --batch-size 64 \
    --device 0 \
    --name stage1_colab_full \
    --project /content/drive/MyDrive/doctor-doom/models
```

### Step 5: Export Model

```python
from ultralytics import YOLO

# Load best model
model = YOLO('/content/drive/MyDrive/doctor-doom/models/stage1_colab/weights/best.pt')

# Export to ONNX
model.export(format='onnx', opset=17)
print("✓ ONNX model exported")

# Export to CoreML (for Mac deployment)
model.export(format='coreml', precision='fp16')
print("✓ CoreML model exported")

# List exported files
!ls -lh /content/drive/MyDrive/doctor-doom/models/stage1_colab/weights/
```

### Step 6: Download Models

```python
# Download to local machine
from google.colab import files

files.download('/content/drive/MyDrive/doctor-doom/models/stage1_colab/weights/best.onnx')
files.download('/content/drive/MyDrive/doctor-doom/models/stage1_colab/weights/best_coreml.mlpackage')

# Or copy to your service directory
!cp /content/drive/MyDrive/doctor-doom/models/stage1_colab/weights/best.onnx \
    /content/drive/MyDrive/doctor-doom/services/ml-inference/models/stage1/model.onnx
```

---

## Complete Colab Notebook Code

Copy this entire block into a Colab notebook:

```python
# ============================================================
# Doctor Doom - Stage 1 Training on Google Colab
# ============================================================

# 1. Check GPU
print("=" * 60)
print("GPU Information:")
print("=" * 60)
!nvidia-smi

# 2. Mount Google Drive
print("\n" + "=" * 60)
print("Mounting Google Drive...")
print("=" * 60)
from google.colab import drive
drive.mount('/content/drive')

# 3. Install dependencies
print("\n" + "=" * 60)
print("Installing dependencies...")
print("=" * 60)
!pip install ultralytics roboflow -q

# 4. Clone or upload project
print("\n" + "=" * 60)
print("Setting up project...")
print("=" * 60)

# Option A: Clone from GitHub
# !git clone https://github.com/your-org/doctor-doom-project.git
# %cd doctor-doom-project/services/ml-inference

# Option B: Use uploaded files
%cd /content/drive/MyDrive/doctor-doom/services/ml-inference

# 5. Prepare dataset
print("\n" + "=" * 60)
print("Preparing dataset...")
print("=" * 60)
!python scripts/prepare_dataset_stage1.py \
    --dataset dataset_1 \
    --output datasets/processed/stage1

# 6. Train model
print("\n" + "=" * 60)
print("Starting training...")
print("=" * 60)
!python scripts/train_stage1.py \
    --data datasets/processed/stage1/data.yaml \
    --epochs 100 \
    --batch-size 32 \
    --device 0 \
    --name stage1_colab \
    --project /content/drive/MyDrive/doctor-doom/models

# 7. Export model
print("\n" + "=" * 60)
print("Exporting model...")
print("=" * 60)
from ultralytics import YOLO

model = YOLO('/content/drive/MyDrive/doctor-doom/models/stage1_colab/weights/best.pt')
model.export(format='onnx')
model.export(format='coreml')

print("\n" + "=" * 60)
print("✅ TRAINING COMPLETE!")
print("=" * 60)
print(f"\nModels saved to:")
print(f"  - ONNX: /content/drive/MyDrive/doctor-doom/models/stage1_colab/weights/best.onnx")
print(f"  - CoreML: /content/drive/MyDrive/doctor-doom/models/stage1_colab/weights/best_coreml.mlpackage")
```

---

## Performance Comparison

| Platform | GPU | Time (50 epochs) | Cost |
|----------|-----|------------------|------|
| **Colab (Free)** | T4 (16GB) | ~15-20 minutes | Free |
| **Colab Pro** | V100 (16GB) | ~8-12 minutes | $10/month |
| **Colab Pro+** | A100 (40GB) | ~5-8 minutes | $50/month |
| **Local M2** | MPS | ~30-40 minutes | Free |
| **Local CPU** | - | ~2-3 hours | Free |

---

## Colab Settings

### GPU Selection

1. Click **Runtime** → **Change runtime type**
2. Select **GPU** from Hardware accelerator
3. Choose GPU type (if available):
   - **T4** - Free tier (good for testing)
   - **V100** - Colab Pro (recommended)
   - **A100** - Colab Pro+ (fastest)

### RAM Management

```python
# Check RAM usage
!free -h

# Clear cache if running low
import gc
gc.collect()

# Clear CUDA cache
import torch
torch.cuda.empty_cache()
```

### Prevent Disconnection

```python
# Keep Colab alive (run in separate cell)
import time
while True:
    time.sleep(1800)  # Prevent timeout
```

**Warning:** Colab may still disconnect after 12 hours (free) or 24 hours (Pro).

---

## Training with Different Datasets

### Dataset from Roboflow

```python
# Install roboflow
!pip install roboflow

from roboflow import Roboflow
rf = Roboflow(api_key="YOUR_API_KEY")
project = rf.workspace("your-workspace").project("solar-panels")
dataset = project.version(1).download("yolov8")

# Train
!python scripts/train_stage1.py \
    --data /content/dataset-1/data.yaml \
    --epochs 100 \
    --batch-size 32 \
    --device 0 \
    --name stage1_roboflow
```

### Custom Dataset

```python
# Upload your dataset
from google.colab import files
uploaded = files.upload()  # Upload your_dataset.zip

# Unzip
!unzip -q your_dataset.zip

# Convert to YOLO format (if needed)
# ... your conversion code ...

# Train
!python scripts/train_stage1.py \
    --data /content/your_dataset/data.yaml \
    --epochs 100 \
    --batch-size 32 \
    --device 0 \
    --name stage1_custom
```

---

## Monitoring Training

### Live Metrics

```python
# Install tensorboard
%load_ext tensorboard

# Start tensorboard
%tensorboard --logdir /content/drive/MyDrive/doctor-doom/models/stage1_colab
```

### View Results

```python
# Display training plots
from IPython.display import Image, display

display(Image(filename='/content/drive/MyDrive/doctor-doom/models/stage1_colab/results.png'))
display(Image(filename='/content/drive/MyDrive/doctor-doom/models/stage1_colab/confusion_matrix.png'))
```

---

## Troubleshooting

### Out of Memory

```python
# Reduce batch size
--batch-size 16  # or 8

# Or clear CUDA cache
import torch
torch.cuda.empty_cache()
```

### Training Too Slow

```python
# Ensure GPU is being used
!nvidia-smi

# Check device in training
import torch
print(f"Using device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
```

### Colab Keeps Disconnecting

1. Use Colab Pro/Pro+ for longer sessions
2. Save checkpoints frequently (already enabled)
3. Save to Google Drive (not local Colab storage)

---

## After Training

### Deploy to Service

```bash
# Copy models to your service
cp /content/drive/MyDrive/doctor-doom/models/stage1_colab/weights/best.onnx \
   /path/to/services/ml-inference/models/stage1/model.onnx

cp /content/drive/MyDrive/doctor-doom/models/stage1_colab/weights/best_coreml.mlpackage \
   /path/to/services/ml-inference/models/stage1/model_coreml.mlpackage

# Verify
python scripts/verify_stage1.py
```

### Update Model Registry

```python
import json
from datetime import datetime

model_info = {
    "name": "module-segmentation-colab",
    "version": "1.0.0",
    "stage": 1,
    "format": "onnx",
    "architecture": "YOLOv8n-seg",
    "input_shape": [640, 512, 1],
    "metrics": {
        "mAP50": 0.95,
        "mAP50-95": 0.75
    },
    "trained_on": "dataset_1",
    "trained_at": datetime.now().isoformat(),
    "trained_with": "Google Colab T4 GPU",
    "description": "Solar module segmentation trained on Colab"
}

with open('models/stage1/model_info.json', 'w') as f:
    json.dump(model_info, f, indent=2)
```

---

## Cost Optimization

### Free Tier Tips
- Train in multiple short sessions (<12 hours)
- Save checkpoints to Google Drive
- Use batch size 16-32 (fits in T4 memory)
- 50-100 epochs usually sufficient for testing

### Colab Pro Worth It?
- ✅ Yes, if training regularly
- ✅ V100 is 2-3x faster than T4
- ✅ Longer session limits (24 hours)
- ✅ More RAM (25GB vs 12GB)

---

## Next Steps

After Stage 1 training:

1. **Deploy model** - Copy to service
2. **Test inference** - Run on sample images
3. **Train Stage 2** - Defect detection
4. **Train Stage 3** - Severity scoring
5. **Train Stage 4** - Anomaly detection

---

**Last Updated:** 2026-03-20  
**Recommended:** Colab Pro (V100) for best price/performance
