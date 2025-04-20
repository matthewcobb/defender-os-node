#!/usr/bin/env python3
"""
Safe‑shutdown monitor for CarPiHAT PRO 5 – Raspberry Pi 5 compatible
"""

from gpiozero import DigitalInputDevice, DigitalOutputDevice
import subprocess
import time

# --- Configuration -----------------------------------------------------------
IGN_PIN       = 12      # BCM12 – ignition / 12 V SW sense
EN_POWER_PIN  = 25      # BCM25 – latch output
IGN_LOW_TIME  = 10      # seconds ignition must stay low before shutdown
POLL_INTERVAL = 0.1     # seconds between polls

# --- GPIO setup --------------------------------------------------------------
# internal pull‑down keeps the pin low when the wire is open;
# high (3 V3) from CarPiHAT = ignition ON
ignition = DigitalInputDevice(IGN_PIN, pull_up=False)

# assert the latch so the HAT keeps 5 V on
latch = DigitalOutputDevice(EN_POWER_PIN, initial_value=True)

print("CarPiHAT power manager started – latch asserted (GPIO25 HIGH).")

low_since = None
try:
    while True:
        if ignition.is_active:          # ignition present
            low_since = None
        else:                           # ignition lost
            if low_since is None:
                low_since = time.monotonic()
            elif time.monotonic() - low_since >= IGN_LOW_TIME:
                print("Ignition low for %ds – shutting down…" % IGN_LOW_TIME)
                subprocess.call(["sudo", "shutdown", "-h", "now"])
                time.sleep(2)           # let the command flush
                break
        time.sleep(POLL_INTERVAL)
finally:
    # drop the latch so the HAT can cut 5 V once the Pi is halted
    latch.off()
    print("Latch dropped – CarPiHAT will remove power.")
