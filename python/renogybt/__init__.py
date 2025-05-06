"""
Simplified Renogy Bluetooth Module for communication with Renogy solar charge controllers and batteries
"""

from .device import Device
from .manager import DeviceManager
from .utils import bytes_to_int, crc16_modbus
from .rover import RoverDevice
from .battery import BatteryDevice
from .lipo_model import LipoModel
__all__ = [
    'Device',
    'DeviceManager',
    'RoverDevice',
    'BatteryDevice',
    'LipoModel',
    'bytes_to_int',
    'crc16_modbus'
]

__version__ = '1.0.0'