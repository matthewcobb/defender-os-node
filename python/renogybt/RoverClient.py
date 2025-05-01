import logging
import asyncio
from .BaseClient import BaseClient
from .Utils import bytes_to_int, parse_temperature
from config.settings import TEMPERATURE_UNIT
# Read and parse BT-1/BT-2 type bluetooth modules connected to Renogy Rover/Wanderer/Adventurer

FUNCTION = {
    3: "READ",
    6: "WRITE"
}

CHARGING_STATE = {
    0: 'deactivated',
    1: 'activated',
    2: 'mppt',
    3: 'equalizing',
    4: 'boost',
    5: 'floating',
    6: 'current limiting'
}

LOAD_STATE = {
  0: 'off',
  1: 'on'
}

BATTERY_TYPE = {
    1: 'open',
    2: 'sealed',
    3: 'gel',
    4: 'lithium',
    5: 'custom'
}

class RoverClient(BaseClient):
    def __init__(self, client_config, on_data_callback=None, on_error_callback=None):
        """Initialize the Rover/DC controller client"""
        super().__init__(client_config, on_data_callback, on_error_callback)
        self.data = {}
        self.sections = [
            {'register': 12, 'words': 8, 'parser': self.parse_device_info},
            {'register': 26, 'words': 1, 'parser': self.parse_device_address},
            {'register': 256, 'words': 34, 'parser': self.parse_chargin_info},
            {'register': 57348, 'words': 1, 'parser': self.parse_battery_type}
        ]
        self.set_load_params = {'function': 6, 'register': 266}
        self.write_lock = asyncio.Lock()
        self.write_future = None

    async def on_data_received(self, response):
        """Handles data received from the device"""
        operation = bytes_to_int(response, 1, 1)
        if operation == 6:  # write operation
            self.parse_set_load_response(response)
            # Complete any pending write future
            if self.write_future and not self.write_future.done():
                self.write_future.set_result(True)

            # Call data callback with the updated data
            if self.on_data_callback:
                await self.on_data_callback(self, self.data)

            # Clear data after callback
            self.data = {}
        else:
            # Read is handled in base class
            await super().on_data_received(response)

    async def set_load(self, value=0):
        """Set the load state (on/off)"""
        async with self.write_lock:
            logging.info(f"Setting load to {value}")

            # Check connection
            if not await self.ble_manager.ensure_connected():
                logging.error("Cannot set load: device not connected")
                return False

            # Create request
            request = self.create_generic_read_request(
                self.device_id,
                self.set_load_params["function"],
                self.set_load_params["register"],
                value
            )

            # Setup response handling
            self.write_future = asyncio.get_event_loop().create_future()

            # Send request
            if not await self.ble_manager.characteristic_write_value(request):
                return False

            # Wait for response
            try:
                await asyncio.wait_for(self.write_future, 5)  # 5 second timeout
                return True
            except asyncio.TimeoutError:
                logging.error("Timeout setting load state")
                return False

    def parse_device_info(self, bs):
        """Parse device information"""
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['model'] = (bs[3:19]).decode('utf-8').strip()
        self.data.update(data)

    def parse_device_address(self, bs):
        """Parse device address/ID"""
        data = {}
        data['device_id'] = bytes_to_int(bs, 4, 1)
        self.data.update(data)

    def parse_chargin_info(self, bs):
        """Parse charging/operating information"""
        data = {}
        temp_unit = TEMPERATURE_UNIT
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['battery_percentage'] = bytes_to_int(bs, 3, 2)
        data['battery_voltage'] = bytes_to_int(bs, 5, 2, scale = 0.1)
        data['battery_current'] = bytes_to_int(bs, 7, 2, scale = 0.01)
        data['battery_temperature'] = parse_temperature(bytes_to_int(bs, 10, 1), temp_unit)
        data['controller_temperature'] = parse_temperature(bytes_to_int(bs, 9, 1), temp_unit)
        data['load_status'] = LOAD_STATE.get(bytes_to_int(bs, 67, 1) >> 7)
        data['load_voltage'] = bytes_to_int(bs, 11, 2, scale = 0.1)
        data['load_current'] = bytes_to_int(bs, 13, 2, scale = 0.01)
        data['load_power'] = bytes_to_int(bs, 15, 2)
        data['pv_voltage'] = bytes_to_int(bs, 17, 2, scale = 0.1)
        data['pv_current'] = bytes_to_int(bs, 19, 2, scale = 0.01)
        data['pv_power'] = bytes_to_int(bs, 21, 2)
        data['max_charging_power_today'] = bytes_to_int(bs, 33, 2)
        data['max_discharging_power_today'] = bytes_to_int(bs, 35, 2)
        data['charging_amp_hours_today'] = bytes_to_int(bs, 37, 2)
        data['discharging_amp_hours_today'] = bytes_to_int(bs, 39, 2)
        data['power_generation_today'] = bytes_to_int(bs, 41, 2)
        data['power_consumption_today'] = bytes_to_int(bs, 43, 2)
        data['power_generation_total'] = bytes_to_int(bs, 59, 4)
        data['charging_status'] = CHARGING_STATE.get(bytes_to_int(bs, 68, 1))
        self.data.update(data)

    def parse_battery_type(self, bs):
        """Parse battery type information"""
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['battery_type'] = BATTERY_TYPE.get(bytes_to_int(bs, 3, 2))
        self.data.update(data)

    def parse_set_load_response(self, bs):
        """Parse response after setting load state"""
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['load_status'] = bytes_to_int(bs, 5, 1)
        self.data.update(data)
