#!/usr/bin/env python3
from gpiozero import DigitalInputDevice
import subprocess, time, sys

IGN_PIN       = 12      # BCM12 – ACC sense (active‑LOW)
IGN_LOW_TIME  = 10      # seconds to wait before shutdown
POLL_INTERVAL = 0.1     # main‑loop tick

# Leave the pin floating (no extra resistor) and declare it *active‑LOW*
ignition = DigitalInputDevice(
    IGN_PIN,
    pull_up=None,       # use the HAT's own 10 k pull‑up
    active_state=False  # pin LOW  -> ignition ACTIVE
)

print("CarPiHAT shutdown monitor running – ignition active while pin is LOW")

low_since = None
try:
    while True:
        if ignition.is_active:                 # ignition present
            low_since = None                   # reset timer
        else:                                  # ignition lost
            if low_since is None:
                low_since = time.monotonic()
            elif time.monotonic() - low_since >= IGN_LOW_TIME:
                print(f"Ignition low for {IGN_LOW_TIME}s – shutting down…")
                subprocess.call(["sudo", "shutdown", "-h", "now"])
                time.sleep(2)
                sys.exit(0)
        time.sleep(POLL_INTERVAL)
except KeyboardInterrupt:
    pass
