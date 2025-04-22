# Configuration settings for the application

# Renogy device configurations
DCDC_CONFIG = {
    'type': 'RNG_CTRL',
    'mac_address': 'AC:4D:16:19:14:1A',
    'name': 'BT-TH-9B26D2DC',
    'device_id': 255
}

BATTERY_CONFIG = {
    'type': 'RNG_BATT',
    'mac_address': 'FC:A8:9B:26:D2:DC',
    'name': 'BT-TH-9B26D2DC',
    'device_id': 255
}

# Paths
import os

# Get the directory of the current script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_DIR = os.path.join(PROJECT_ROOT, 'app')

# Server settings
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000