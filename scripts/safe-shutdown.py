#!/usr/bin/env python3
from gpiozero import DigitalInputDevice
import subprocess, time, sys

IGN_PIN       = 12      # BCM12 – ACC sense (active‑LOW)
IGN_LOW_TIME  = 10      # seconds to wait before shutdown
POLL_INTERVAL = 0.1     # main‑loop tick

# Leave the pin floating (no extra resistor) and declare it *active‑LOW*
ignition = DigitalInputDevice(
    IGN_PIN,
    pull_up=None,        # no extra resistor
    active_state=True    # pin HIGH → ignition present
)

print("CarPiHAT shutdown monitor running – ignition active while pin is LOW")

low_since = None
countdown_shown = False
try:
    while True:
        if ignition.is_active:                 # ignition present
            if low_since is not None:
                print("Ignition restored - shutdown canceled")
            low_since = None                   # reset timer
            countdown_shown = False
        else:                                  # ignition lost
            if low_since is None:
                print("Ignition lost - starting shutdown countdown")
                low_since = time.monotonic()
            else:
                time_elapsed = time.monotonic() - low_since
                time_remaining = max(0, IGN_LOW_TIME - time_elapsed)

                # Show countdown in whole seconds when the value changes
                if int(time_remaining) < IGN_LOW_TIME and not countdown_shown or int(time_remaining) != int(IGN_LOW_TIME - time_elapsed + POLL_INTERVAL):
                    print(f"Shutdown in {int(time_remaining)} seconds...")
                    countdown_shown = True

                if time_elapsed >= IGN_LOW_TIME:
                    print(f"Ignition low for {IGN_LOW_TIME}s – shutting down…")
                    subprocess.call(["sudo", "shutdown", "-h", "now"])
                    time.sleep(2)
                    sys.exit(0)
        time.sleep(POLL_INTERVAL)
except KeyboardInterrupt:
    pass
