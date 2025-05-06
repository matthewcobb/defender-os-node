"""
Simplified client for Renogy Rover/Wanderer/Adventurer controllers
"""

import logging
from typing import Dict, Any, Optional

from .device import Device
from .utils import bytes_to_int, parse_temperature, CHARGING_STATES, LOAD_STATES, BATTERY_TYPES
from config.settings import TEMPERATURE_UNIT

class RoverDevice(Device):
    """
    Specialized device implementation for Renogy Rover/Wanderer/Adventurer controllers
    """

    def __init__(self, mac_address: str, name: str = None, device_id: int = 1, **kwargs):
        """
        Initialize a Rover controller device

        Args:
            mac_address: MAC address of the device
            name: Name/alias of the device (default: based on MAC)
            device_id: Modbus device ID (default: 1)
        """
        super().__init__(mac_address, name, device_id, **kwargs)
        self.temperature_unit = TEMPERATURE_UNIT

        # Define register sections to poll
        self.add_section(register=12, word_count=8, parser=self.parse_device_info)
        self.add_section(register=26, word_count=1, parser=self.parse_device_address)
        self.add_section(register=256, word_count=34, parser=self.parse_charging_info)
        self.add_section(register=57348, word_count=1, parser=self.parse_battery_type)

    async def set_load(self, state: bool = False) -> bool:
        """
        Set the load state (on/off)

        Args:
            state: True for on, False for off

        Returns:
            bool: True if successful
        """
        value = 1 if state else 0
        logging.info(f"🔌 Setting load to {'ON' if state else 'OFF'}")
        return await self.write_register(register=266, value=value)

    def parse_device_info(self, data: bytearray) -> None:
        """
        Parse device information

        Args:
            data: Raw response data
        """
        # Extract model name (bytes 3-19)
        try:
            model = data[3:19].decode('utf-8').strip()
            self.data['model'] = model
        except Exception as e:
            logging.error(f"❌ Error parsing device info: {e}")

    def parse_device_address(self, data: bytearray) -> None:
        """
        Parse device address/ID

        Args:
            data: Raw response data
        """
        try:
            self.data['device_id'] = bytes_to_int(data, 4, 1)
        except Exception as e:
            logging.error(f"❌ Error parsing device address: {e}")

    def parse_charging_info(self, data: bytearray) -> None:
        """
        Parse charging and operating information

        Args:
            data: Raw response data
        """
        try:
            # Battery info
            self.data['battery_percentage'] = bytes_to_int(data, 3, 2)
            self.data['battery_voltage'] = bytes_to_int(data, 5, 2, scale=0.1)
            self.data['battery_current'] = bytes_to_int(data, 7, 2, scale=0.01)
            self.data['battery_temperature'] = parse_temperature(bytes_to_int(data, 10, 1), self.temperature_unit)

            # Controller info
            self.data['controller_temperature'] = parse_temperature(bytes_to_int(data, 9, 1), self.temperature_unit)
            self.data['charging_status'] = CHARGING_STATES.get(bytes_to_int(data, 68, 1), 'unknown')

            # Load info
            load_status_bit = bytes_to_int(data, 67, 1) >> 7
            self.data['load_status'] = LOAD_STATES.get(load_status_bit, 'unknown')
            self.data['load_voltage'] = bytes_to_int(data, 11, 2, scale=0.1)
            self.data['load_current'] = bytes_to_int(data, 13, 2, scale=0.01)
            self.data['load_power'] = bytes_to_int(data, 15, 2)

            # PV (solar) info
            self.data['pv_voltage'] = bytes_to_int(data, 17, 2, scale=0.1)
            self.data['pv_current'] = bytes_to_int(data, 19, 2, scale=0.01)
            self.data['pv_power'] = bytes_to_int(data, 21, 2)

            # Daily stats
            self.data['max_charging_power_today'] = bytes_to_int(data, 33, 2)
            self.data['max_discharging_power_today'] = bytes_to_int(data, 35, 2)
            self.data['charging_amp_hours_today'] = bytes_to_int(data, 37, 2)
            self.data['discharging_amp_hours_today'] = bytes_to_int(data, 39, 2)
            self.data['power_generation_today'] = bytes_to_int(data, 41, 2)
            self.data['power_consumption_today'] = bytes_to_int(data, 43, 2)

            # Total stats
            self.data['power_generation_total'] = bytes_to_int(data, 59, 4)
        except Exception as e:
            logging.error(f"❌ Error parsing charging info: {e}")

    def parse_battery_type(self, data: bytearray) -> None:
        """
        Parse battery type information

        Args:
            data: Raw response data
        """
        try:
            battery_type_code = bytes_to_int(data, 3, 2)
            self.data['battery_type'] = BATTERY_TYPES.get(battery_type_code, 'unknown')
        except Exception as e:
            logging.error(f"❌ Error parsing battery type: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the device state

        Returns:
            dict: Summary of key device parameters
        """
        summary = {}

        # Include key fields if available
        for key in [
            'model', 'battery_percentage', 'battery_voltage',
            'pv_power', 'load_power', 'charging_status', 'load_status',
            'battery_temperature', 'controller_temperature'
        ]:
            if key in self.data:
                summary[key] = self.data[key]

        return summary