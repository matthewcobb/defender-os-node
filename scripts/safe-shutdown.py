#!/usr/bin/env python3
from gpiozero import DigitalInputDevice
import subprocess, time, sys

IGN_PIN       = 12          # ACC / 12 V SW sense
IGN_LOW_TIME  = 10          # seconds low before shutdown
POLL          = 0.1         # s

ignition = DigitalInputDevice(IGN_PIN, pull_up=False)  # internal pull‑down
low_since = None

while True:
    if ignition.is_active:          # ignition present
        low_since = None
    else:                           # ignition lost
        if low_since is None:
            low_since = time.monotonic()
        elif time.monotonic() - low_since >= IGN_LOW_TIME:
            subprocess.call(["sudo", "shutdown", "-h", "now"])
            time.sleep(2)
            sys.exit(0)
    time.sleep(POLL)
