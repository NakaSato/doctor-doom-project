#!/bin/bash
# Monitor ML Training Progress
# Usage: ./monitor_training.sh

LOG_FILE="/tmp/ml_full_training.log"

echo "=============================================="
echo "Doctor Doom ML Training Monitor"
echo "=============================================="
echo ""
echo "Log file: $LOG_FILE"
echo "Checking every 30 seconds..."
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    echo "----------------------------------------"
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "Last 20 lines of log:"
        tail -20 "$LOG_FILE" 2>/dev/null
        
        echo ""
        echo "Training Progress:"
        grep -E "(Epoch|Stage|Training|Complete)" "$LOG_FILE" 2>/dev/null | tail -10
        
        echo ""
        echo "Log file size: $(wc -l < "$LOG_FILE") lines, $(du -h "$LOG_FILE" | cut -f1)"
    else
        echo "Log file not found. Training may not have started."
    fi
    
    echo ""
    sleep 30
done
