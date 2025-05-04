# Configuration settings for the application

# Renogy device configurations
DCDC_CONFIG = {
    'adapter': 'hci0',
    'type': 'rng_ctrl',
    'mac_addr': 'F9A78286-C476-FAFA-B979-8A15259A1768',
    'alias': 'BT-TH-1619141A',
    'device_id': 255
}

BATTERY_CONFIG = {
    'adapter': 'hci0',
    'type': 'rng_batt',
    'mac_addr': '7BD4C7F0-B018-68EA-BBAD-7D21D527310D',
    'alias': 'BT-TH-9B26D2DC',
    'device_id': 255
}

# Renogy
POLL_INTERVAL = 5  # seconds - increased from 5s to reduce Raspberry Pi BLE load
TEMPERATURE_UNIT = 'C'

# WiFi favorites
WIFI_FAVORITES = [
    {
        "ssid": "Matthew Cobb's iPhone",
        "password": "",  # If empty, will try to connect using saved credentials
        "auto_connect": True
    }
]

# Paths
import os

# Get the directory of the current script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_DIR = os.path.join(PROJECT_ROOT, 'app')

# Server settings
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000

# GPIO settings
REVERSE_PIN = 7
DEVELOPMENT_MODE = False  # Set to True for development without GPIO hardware