#!/bin/bash
# ML Training Runner for Doctor Doom
# Runs training with system Python (torch installed globally)

set -e

echo "============================================================"
echo "Doctor Doom ML Model Training"
echo "============================================================"
echo ""

# Use system Python (torch is installed there)
PYTHON="/usr/local/bin/python"
TRAIN_SCRIPT="/app/train_models.py"

# Parse arguments or use defaults
EPOCHS=${1:-50}
BATCH_SIZE=${2:-32}
NUM_SAMPLES=${3:-10000}
DEVICE=${4:-cpu}

echo "Configuration:"
echo "  Epochs: $EPOCHS"
echo "  Batch Size: $BATCH_SIZE"
echo "  Samples: $NUM_SAMPLES"
echo "  Device: $DEVICE"
echo ""

# Check Python and dependencies
echo "Checking dependencies..."
$PYTHON -c "import torch; print(f'  PyTorch: {torch.__version__}')"
$PYTHON -c "import numpy; print(f'  NumPy: {numpy.__version__}')"
$PYTHON -c "import tqdm; print('  tqdm: OK')"
echo ""

# Run training
echo "Starting training..."
$PYTHON $TRAIN_SCRIPT \
    --epochs $EPOCHS \
    --batch-size $BATCH_SIZE \
    --num-samples $NUM_SAMPLES \
    --device $DEVICE

echo ""
echo "============================================================"
echo "Training Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Export models: python /app/export_models.py"
echo "2. Rebuild container with trained models"
echo "3. Test inference: curl http://localhost:8001/health"
