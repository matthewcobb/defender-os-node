#!/usr/bin/env python3
from gpiozero import DigitalInputDevice
import subprocess, time, sys

IGN_PIN       = 12          # ACC / 12 V SW sense
IGN_LOW_TIME  = 10          # seconds low before shutdown
POLL          = 0.1         # s

# Initialize ignition pin with pull_up=False for internal pull-down
ignition = DigitalInputDevice(IGN_PIN, pull_up=False)
low_since = None
print("Safe shutdown script started. Monitoring ignition state on pin", IGN_PIN)

try:
    while True:
        if ignition.is_active:          # ignition present
            if low_since is not None:
                print("Ignition restored - canceling shutdown timer")
            low_since = None
        else:                           # ignition lost
            if low_since is None:
                print(f"Ignition lost - starting {IGN_LOW_TIME} second countdown")
                low_since = time.monotonic()
            else:
                elapsed = time.monotonic() - low_since
                remaining = IGN_LOW_TIME - elapsed

                # Only print every full second to avoid log spam
                if int(elapsed) != int(elapsed - POLL) and remaining > 0:
                    print(f"Shutdown in {remaining:.1f} seconds...")

                if elapsed >= IGN_LOW_TIME:
                    print("Shutdown countdown complete - shutting down now")
                    subprocess.call(["sudo", "shutdown", "-h", "now"])
                    time.sleep(2)
                    sys.exit(0)
        time.sleep(POLL)
except KeyboardInterrupt:
    print("Script terminated by user")
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
