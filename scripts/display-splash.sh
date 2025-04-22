#!/bin/bash

# Path to splash image
SPLASH_IMAGE="/home/pi/defender-os-node/boot/background.jpg"

# Ensure we have a place to store the PID
mkdir -p /tmp

# For Wayland, we use swaybg instead of feh
swaybg -i "$SPLASH_IMAGE" -m fill &

# Save the process ID so we can kill it later
echo $! > /tmp/splash-pid.txt