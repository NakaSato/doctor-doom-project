# Quick Start: Train Stage 1 on Colab

## 🚀 Fastest Way (5 Minutes Setup)

### 1. Open Colab
Click here: [Open Stage1_Colab_Training.ipynb in Colab](https://colab.research.google.com/github/your-org/doctor-doom-project/blob/main/services/ml-inference/Stage1_Colab_Training.ipynb)

Or manually:
1. Go to https://colab.research.google.com
2. Upload `Stage1_Colab_Training.ipynb`

### 2. Run All Cells
Click **Runtime** → **Run all**

That's it! Training completes in **15-20 minutes** on free Colab.

---

## 📋 What You Need

1. **Google Account** (free)
2. **dataset_1** folder (120 images + annotations)
3. **15-20 minutes** (Colab Free T4 GPU)

---

## 📊 Expected Results

| Metric | Target |
|--------|--------|
| **mAP@50** | ≥95% |
| **mAP@50-95** | ≥75% |
| **Training Time** | 15-20 min |
| **Model Size** | ~6 MB (ONNX) |

---

## 💾 After Training

Models saved to:
- Google Drive: `/doctor-doom/models/stage1_colab/weights/`
- Formats: `.pt`, `.onnx`, `.mlpackage`

### Deploy to Service

```bash
# Copy from Drive to your project
cp /content/drive/MyDrive/doctor-doom/models/stage1_colab/weights/best.onnx \
   services/ml-inference/models/stage1/model.onnx

# Verify
cd services/ml-inference
python scripts/verify_stage1.py
```

---

## 🔧 Troubleshooting

### Out of Memory
Reduce batch size in Step 4:
```python
BATCH_SIZE = 16  # or 8
```

### Colab Disconnects
- Save checkpoints to Google Drive (already configured)
- Use Colab Pro for longer sessions (24 hours vs 12 hours)

### Training Too Slow
Ensure GPU is selected:
1. Click **Runtime** → **Change runtime type**
2. Select **GPU** accelerator

---

## 📈 Performance

| Platform | GPU | Time | Cost |
|----------|-----|------|------|
| Colab Free | T4 | 20 min | Free ✅ |
| Colab Pro | V100 | 10 min | $10/mo |
| Colab Pro+ | A100 | 5 min | $50/mo |
| Local M2 | MPS | 40 min | Free |

---

## 📚 Full Documentation

- `COLAB_TRAINING_GUIDE.md` - Complete guide
- `Stage1_Colab_Training.ipynb` - Ready-to-use notebook
- `STAGE1_DEPLOYMENT.md` - Deployment instructions

---

**Last Updated:** 2026-03-20  
**Recommended:** Colab Free T4 (best value)
