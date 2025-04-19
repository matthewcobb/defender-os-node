#!/bin/bash
chromium-browser http://localhost:3000 \
  --kiosk \
  --no-sandbox \
  --disable-web-security \
  --disable-webusb-security \
  --disable-extensions \
  --autoplay-policy=no-user-gesture-required \
  --window-size=1600,600 \
  --start-fullscreen \
  --default-background-color=000000 &
