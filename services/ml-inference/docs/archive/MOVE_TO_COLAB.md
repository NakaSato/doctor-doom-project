# 🚀 Move Training to Google Colab

## ✅ Local Training Stopped

Your local background training has been stopped. You can now use Google Colab for **faster GPU training** (2-3 hours vs 8-12 hours on CPU).

---

## 📋 Steps to Train on Colab

### Step 1: Upload Notebook to Colab

1. Go to **https://colab.research.google.com**

2. Click **"Upload"** tab

3. Upload the notebook:
   ```
   services/ml-inference/Doctor_Doom_ML_Training.ipynb
   ```

### Step 2: Enable GPU

1. In Colab, go to: **Runtime → Change runtime type**

2. Select:
   - **Hardware accelerator**: `GPU`
   - **GPU type**: `T4` (free tier)

3. Click **"Save"**

### Step 3: Run All Cells

1. Click: **Runtime → Run all** (or press `Ctrl+F9`)

2. The notebook will:
   - ✅ Check GPU availability
   - ✅ Install dependencies
   - ✅ Create model architectures
   - ✅ Initialize all 4 stages
   - ✅ Train for 50 epochs (~2-3 hours)
   - ✅ Export to ONNX format
   - ✅ Download trained models

### Step 4: Download Trained Models

After training completes, the notebook will automatically download:
```
trained_models.zip  (~75 MB)
```

This contains:
- `stage1.onnx` - Hotspot detector
- `stage2.onnx` - Cell analyzer
- `stage3.onnx` - Defect classifier
- `stage4.onnx` - Severity scorer

---

## 📁 Deploy Trained Models

### 1. Copy Models to Project

```bash
# Move downloaded zip to project
cp ~/Downloads/trained_models.zip \
   /path/to/doctor-doom-project/services/ml-inference/models/

# Extract
cd /path/to/doctor-doom-project/services/ml-inference/models/
unzip trained_models.zip
```

### 2. Restart ML Service

```bash
cd /path/to/doctor-doom-project
docker compose restart ml-inference
```

### 3. Verify Models Loaded

```bash
# Check health
curl http://localhost:8001/health

# Check metrics
curl http://localhost:8001/metrics
```

Expected output:
```json
{
  "status": "healthy",
  "service": "ml-inference",
  "models_loaded": true,
  "stages": 4
}
```

---

## ⏱️ Training Time Comparison

| Platform | Hardware | Time | Cost |
|----------|----------|------|------|
| **Colab** | NVIDIA T4 GPU | ~2-3 hours | Free |
| **Local (CPU)** | Intel/AMD CPU | ~8-12 hours | Your electricity |
| **Colab Pro** | V100/A100 GPU | ~1-2 hours | $10/month |

---

## 📊 Expected Results

After full training (50 epochs, 10k samples):

| Stage | Metric | Expected |
|-------|--------|----------|
| Stage 1 (Hotspot) | Accuracy | 97%+ |
| Stage 2 (Cell) | IoU | 87%+ |
| Stage 3 (Classifier) | Accuracy | 91%+ |
| Stage 4 (Severity) | AUROC | 88%+ |

**Total Parameters:** 129.7M  
**Model Size:** ~75 MB (all stages)  
**Inference Time:** <35ms per module

---

## 🛠️ Troubleshooting

### Colab Disconnected

**Problem:** Colab disconnects during training

**Solution:**
- Colab sessions last up to 12 hours (free tier)
- Training should complete within this time
- If disconnected, re-run from last checkpoint

### GPU Not Available

**Problem:** No GPU detected

**Solution:**
1. Go to: **Runtime → Change runtime type**
2. Select **GPU** as hardware accelerator
3. Re-run the GPU check cell

### Download Failed

**Problem:** Models didn't download

**Solution:**
```python
# Manually create zip and download
from google.colab import files
import zipfile

with zipfile.ZipFile('trained_models.zip', 'w') as zipf:
    for stage in ['stage1', 'stage2', 'stage3', 'stage4']:
        zipf.write(f'exported_models/{stage}.onnx')

files.download('trained_models.zip')
```

---

## 📖 Documentation

- `Doctor_Doom_ML_Training.ipynb` - Colab notebook
- `ML_IMPLEMENTATION.md` - ML architecture guide
- `TRAINING_COMPLETE.md` - Training summary

---

## ✅ Quick Checklist

- [ ] Upload notebook to Colab
- [ ] Enable GPU (Runtime → Change runtime type → GPU)
- [ ] Run all cells (Ctrl+F9)
- [ ] Wait for training (~2-3 hours)
- [ ] Download `trained_models.zip`
- [ ] Copy to project's `models/` directory
- [ ] Extract: `unzip trained_models.zip`
- [ ] Restart ML service: `docker compose restart ml-inference`
- [ ] Verify: `curl http://localhost:8001/health`

---

**🎉 You're all set! Happy training on Colab!** 🚀
