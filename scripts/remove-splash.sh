#!/bin/bash

# Check if the PID file exists and kill the process
if [ -f /tmp/splash-pid.txt ]; then
    # Read the PID
    PID=$(cat /tmp/splash-pid.txt)

    # Kill the process
    kill $PID 2>/dev/null || true

    # Remove the PID file
    rm /tmp/splash-pid.txt
fi

# Additionally, make sure all Python splash processes are stopped
pkill -f "python3.*splash-overlay.py" 2>/dev/null || true