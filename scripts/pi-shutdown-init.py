# ------------------------------------------
# init.py
from gpiozero import Button
import time

button = Button(12, pull_up=False)
button.close()

print("Initiated carPiHat GPIO 12")