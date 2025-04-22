#!/bin/bash

# Path to splash image
SPLASH_IMAGE="/home/pi/defender-os-node/boot/background.jpg"

# Use GTK overlay app for a proper fullscreen overlay
chmod +x /home/pi/defender-os-node/scripts/splash-overlay.py
/home/pi/defender-os-node/scripts/splash-overlay.py "$SPLASH_IMAGE" &

# Save the process ID
echo $! > /tmp/splash-pid.txt