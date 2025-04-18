# sudo nano /etc/systemd/system/carpihat.service
[Unit]
Description=CarPiHat initialisation

[Service]
Type=simple

ExecStart=/usr/bin/python3 /home/pi/boot/carPiHat.py
WorkingDirectory=/home/pi/boot/

[Install]
WantedBy=multi-user.target

# ------------------------------------------
# init.py
from gpiozero import Button
import time

button = Button(12, pull_up=False)
button.close()

print("Initiated carPiHat GPIO 12")

# -------------------------------------------
# carpihat.py
import gpiod
import time
from subprocess import call
import subprocess

filename = 'carPiHatInit.py'
subprocess.run(['python3', filename])

print("Running carPiHat.py")

IGN_PIN = 12
IGN_LOW_TIME = 60

chip = gpiod.Chip('gpiochip4')
ign_line = chip.get_line(IGN_PIN)
ign_line.request(consumer="CarPiHat", type=gpiod.LINE_REQ_DIR_IN)

ignLowCounter = 0
ignInitialState = ign_line.get_value()

# Only proceed if the ignition pin is found when initialising.
# This means that if at boot the pin is low, the shurdown will not be triggered.
if ignInitialState == 1:
    try:
        while True:
            ign_state = ign_line.get_value()
            if ign_state == 1:
                print("Plugged")
            else:
                print("Unplugged...")
                time.sleep(1)
                ignLowCounter += 1
                if ignLowCounter > IGN_LOW_TIME:
                    print("Shutting Down")
                    call("sudo shutdown -h now", shell=True)
            time.sleep(0.5)
    finally:
        ign_line.release()
else:
    print("CarPiHat not initiated. Ignition pin not found. Exiting...")
    ign_line.release()
