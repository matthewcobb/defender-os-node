#!/bin/bash

# Ensure we're looking in the right place
if [ ! -d "/tmp" ]; then
    echo "Warning: /tmp directory doesn't exist" >&2
    exit 0
fi

# Check if the PID file exists
if [ -f /tmp/splash-pid.txt ]; then
    # Read the PID
    PID=$(cat /tmp/splash-pid.txt)

    # Check if the process is still running
    if kill -0 $PID 2>/dev/null; then
        # Kill the process
        kill $PID 2>/dev/null || true
        echo "Splash screen process $PID terminated"
    else
        echo "Process $PID not running"
    fi

    # Remove the PID file
    rm /tmp/splash-pid.txt
else
    echo "No splash screen PID file found"
fi

exit 0