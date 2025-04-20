#!/usr/bin/env python3
"""
carpihat_power.py – Safe‑shutdown monitor for CarPiHAT PRO 5
Tested on Raspberry Pi 5 (Bookworm, 64‑bit).

• Pulls GPIO 25 HIGH to latch power on the CarPiHAT.
• Monitors GPIO 12 (ignition sense).
  – If IGN goes low for IGN_LOW_TIME seconds, the Pi is told to shut down.
• After issuing the shutdown command the script drops the latch so the HAT
  removes 5 V completely once the Pi has halted.

Install deps (already present on a standard image, but just in case):
    sudo apt update
    sudo apt install python3-gpiozero
"""

from gpiozero import DigitalInputDevice, DigitalOutputDevice
import subprocess
import time

# --- Pin assignments ---------------------------------------------------------
IGN_PIN        = 12   # BCM12  – 12 V switched input from CarPiHAT
EN_POWER_PIN   = 25   # BCM25 – latch output back to CarPiHAT
IGN_LOW_TIME   = 10   # seconds ignition must stay low before shutdown
POLL_INTERVAL  = 0.5  # seconds between polls (500)

# --- GPIO setup --------------------------------------------------------------
ignition = DigitalInputDevice(IGN_PIN, pull_up=False, active_state=True)
latch    = DigitalOutputDevice(EN_POWER_PIN,
                               active_high=True,
                               initial_value=True)   # latch ON

print("CarPiHAT power manager started – latch asserted (GPIO25 HIGH).")

# --- Main loop ---------------------------------------------------------------
low_since = None
try:
    while True:
        if ignition.is_active:
            # Ignition (ACC/12 V SW) present → keep running
            low_since = None
        else:
            # Ignition off → start / continue countdown
            if low_since is None:
                low_since = time.monotonic()
            elif time.monotonic() - low_since >= IGN_LOW_TIME:
                print(f"Ignition low for {IGN_LOW_TIME}s – shutting down…")
                subprocess.call(["sudo", "shutdown", "-h", "now"])
                time.sleep(2)          # give the command a moment to flush
                break

        time.sleep(POLL_INTERVAL)

finally:
    # Drop the latch so the HAT can cut 5 V once the Pi is halted
    latch.off()
    print("Latch dropped – CarPiHAT will remove power.")
