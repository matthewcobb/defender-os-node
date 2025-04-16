# Disable screen blanking and power management
xset -dpms         # Disable DPMS (display power management)
xset s off         # Disable screen saver
xset s noblank     # Prevent the display from blanking

# Start the window manager (optional for kiosks, but prevents the X server from closing immediately)
matchbox-window-manager -use_titlebar no &  # Minimal window manager (optional)
unclutter -idle 0.5 -root &                 # Hide the mouse cursor after 0.5 seconds

# Show the splash screen (logo image) for 5 seconds
feh --bg-fill /home/pi/defender-os-node/boot/logo.jpg --scale-down --quiet --fullscreen &

# Wait for the splash to be visible for a few seconds (adjust the timing as needed)
sleep 5

# Kill the splash screen
pkill feh

# Launch Chromium in kiosk mode
chromium-browser --kiosk --noerrdialogs http://localhost:3000 --disable-background-networking --disable-webusb-security --disable-extensions --window-size=1600,600

# The Juice
# chromium-browser --kiosk --noerrdialogs http://localhost:3000 --disable-background-networking --disable-webusb-security --disable-extensions --window-size=1600,600 --start-fullscreen
