"""
Simplified client for Renogy LFP batteries with Bluetooth
"""

import logging
from typing import Dict, Any, Optional

from .device import Device
from .utils import bytes_to_int, parse_temperature
from config.settings import TEMPERATURE_UNIT

class BatteryDevice(Device):
    """
    Specialized device implementation for Renogy LFP batteries
    """

    def __init__(self, mac_address: str, name: str = None, device_id: int = 1, **kwargs):
        """
        Initialize a battery device

        Args:
            mac_address: MAC address of the device
            name: Name/alias of the device (default: based on MAC)
            device_id: Modbus device ID (default: 1)
        """
        super().__init__(mac_address, name, device_id, **kwargs)
        self.temperature_unit = TEMPERATURE_UNIT

        # Define register sections to poll
        self.add_section(register=5000, word_count=17, parser=self.parse_cell_volt_info)
        self.add_section(register=5017, word_count=17, parser=self.parse_cell_temp_info)
        self.add_section(register=5042, word_count=6, parser=self.parse_battery_info)
        self.add_section(register=5122, word_count=8, parser=self.parse_device_info)
        self.add_section(register=5223, word_count=1, parser=self.parse_device_address)

    def parse_cell_volt_info(self, data: bytearray) -> None:
        """
        Parse individual cell voltage information

        Args:
            data: Raw response data
        """
        try:
            cell_count = bytes_to_int(data, 3, 2)
            self.data['cell_count'] = cell_count

            # Parse individual cell voltages
            for i in range(0, cell_count):
                self.data[f'cell_voltage_{i}'] = bytes_to_int(data, 5 + i*2, 2, scale=0.1)

            # Calculate min/max/avg cell voltages for convenience
            cell_voltages = [self.data[f'cell_voltage_{i}'] for i in range(cell_count)]
            if cell_voltages:
                self.data['min_cell_voltage'] = min(cell_voltages)
                self.data['max_cell_voltage'] = max(cell_voltages)
                self.data['avg_cell_voltage'] = sum(cell_voltages) / len(cell_voltages)
                self.data['cell_voltage_diff'] = self.data['max_cell_voltage'] - self.data['min_cell_voltage']

        except Exception as e:
            logging.error(f"❌ Error parsing cell voltage info: {e}")

    def parse_cell_temp_info(self, data: bytearray) -> None:
        """
        Parse temperature sensor information

        Args:
            data: Raw response data
        """
        try:
            sensor_count = bytes_to_int(data, 3, 2)
            self.data['sensor_count'] = sensor_count

            # Parse individual temperature sensors
            temperatures = []
            for i in range(0, sensor_count):
                celsius = bytes_to_int(data, 5 + i*2, 2, scale=0.1, signed=True)
                temp_value = celsius if self.temperature_unit.upper() == 'C' else (celsius * 9/5) + 32
                self.data[f'temperature_{i}'] = temp_value
                temperatures.append(temp_value)

            # Calculate min/max/avg temperatures for convenience
            if temperatures:
                self.data['min_temperature'] = min(temperatures)
                self.data['max_temperature'] = max(temperatures)
                self.data['avg_temperature'] = sum(temperatures) / len(temperatures)

        except Exception as e:
            logging.error(f"❌ Error parsing temperature info: {e}")

    def parse_battery_info(self, data: bytearray) -> None:
        """
        Parse battery status information

        Args:
            data: Raw response data
        """
        try:
            # Basic battery metrics
            self.data['current'] = bytes_to_int(data, 3, 2, signed=True, scale=0.01)
            self.data['voltage'] = bytes_to_int(data, 5, 2, scale=0.1)
            self.data['remaining_charge'] = bytes_to_int(data, 7, 4, scale=0.001)
            self.data['capacity'] = bytes_to_int(data, 11, 4, scale=0.001)

            # Calculate derived metrics
            if self.data.get('capacity', 0) > 0:
                self.data['soc_percent'] = min(100, round((self.data['remaining_charge'] / self.data['capacity']) * 100, 1))
            else:
                self.data['soc_percent'] = 0

            # Calculate power (watts)
            self.data['power'] = round(self.data['voltage'] * self.data['current'], 2)

            # Determine if charging or discharging
            if self.data['current'] > 0:
                self.data['status'] = 'charging'
            elif self.data['current'] < 0:
                self.data['status'] = 'discharging'
            else:
                self.data['status'] = 'idle'

        except Exception as e:
            logging.error(f"❌ Error parsing battery info: {e}")

    def parse_device_info(self, data: bytearray) -> None:
        """
        Parse device model information

        Args:
            data: Raw response data
        """
        try:
            # Extract model name from bytes 3-19, strip null characters
            model = data[3:19].decode('utf-8').rstrip('\x00')
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
            self.data['device_id'] = bytes_to_int(data, 3, 2)
        except Exception as e:
            logging.error(f"❌ Error parsing device address: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the battery state

        Returns:
            dict: Summary of key battery parameters
        """
        summary = {}

        # Include key fields if available
        for key in [
            'model', 'voltage', 'current', 'power', 'soc_percent',
            'capacity', 'remaining_charge', 'status',
            'min_cell_voltage', 'max_cell_voltage', 'cell_voltage_diff',
            'min_temperature', 'max_temperature'
        ]:
            if key in self.data:
                summary[key] = self.data[key]

        return summary

    def get_cell_voltages(self) -> Dict[int, float]:
        """
        Get all cell voltages as a dictionary

        Returns:
            dict: Dictionary of cell index to voltage
        """
        result = {}
        cell_count = self.data.get('cell_count', 0)

        for i in range(cell_count):
            key = f'cell_voltage_{i}'
            if key in self.data:
                result[i] = self.data[key]

        return result

    def get_temperatures(self) -> Dict[int, float]:
        """
        Get all temperature sensor readings as a dictionary

        Returns:
            dict: Dictionary of sensor index to temperature
        """
        result = {}
        sensor_count = self.data.get('sensor_count', 0)

        for i in range(sensor_count):
            key = f'temperature_{i}'
            if key in self.data:
                result[i] = self.data[key]

        return result