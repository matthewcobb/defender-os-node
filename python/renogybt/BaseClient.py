import asyncio
import logging
from .BleManager import BleManager
from .Utils import bytes_to_int, crc16_modbus, int_to_bytes
from config.settings import POLL_INTERVAL
# Base class that works with all Renogy family devices
# Should be extended by each client with its own parsers and section definitions
# Section example: {'register': 5000, 'words': 8, 'parser': self.parser_func}

ALIAS_PREFIXES = ['BT-TH', 'RNGRBP', 'BTRIC']
WRITE_SERVICE_UUID = "0000ffd0-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID  = "0000ffd1-0000-1000-8000-00805f9b34fb"
READ_TIMEOUT = 15 # (seconds)
READ_SUCCESS = 3
READ_ERROR = 131

class BaseClient:
    def __init__(self, client_config, on_data_callback=None, on_error_callback=None):
        """Initialize the client with configuration and callbacks"""
        self.client_config = client_config
        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback
        self.ble_manager = BleManager(
            mac_address=self.client_config.get('mac_addr'),
            alias=self.client_config.get('alias'),
            on_data=self.on_data_received,
            on_connect_fail=self.on_connect_fail,
            notify_char_uuid=NOTIFY_CHAR_UUID,
            write_char_uuid=WRITE_CHAR_UUID,
            write_service_uuid=WRITE_SERVICE_UUID
        )
        self.data = {}
        self.device_id = self.client_config.get('device_id')
        self.alias = self.client_config.get('alias')
        self.sections = []
        self.section_index = 0
        self.polling = False
        self.polling_task = None
        logging.info(f"Initialized {self.__class__.__name__}: {self.alias}")

    async def on_connect_fail(self, manager, error):
        """Handle connection failure"""
        logging.error(f"Connection failed: {error}")
        if self.on_error_callback:
            await self.on_error_callback(self, error)

    async def on_data_received(self, data):
        """Handle data received from device"""
        # Parse and handle response protocol
        function_code = data[1]
        if function_code == READ_ERROR:
            error = f"Device reported error: {data.hex()}"
            logging.error(error)
            if self.on_error_callback:
                await self.on_error_callback(self, error)
            return

        # Process response for read function
        if function_code == READ_SUCCESS and len(data) > 5:
            try:
                section = self.sections[self.section_index]
                if section.get('parser'):
                    section['parser'](data)
            except Exception as e:
                logging.error(f"Error parsing data: {e}")
            finally:
                # Trigger next section read if polling is active
                if self.polling:
                    self.section_index = (self.section_index + 1) % len(self.sections)
                    # Notify data callback after fully received data
                    if self.section_index == 0 and self.on_data_callback:
                        # Make a copy to avoid reference issues
                        await self.on_data_callback(self, self.data.copy())

    async def start_polling(self):
        """Start polling the device for data updates"""
        if self.polling:
            logging.warning(f"Already polling device: {self.alias}")
            return

        if not self.ble_manager or not self.ble_manager.is_connected:
            logging.error(f"Cannot start polling: {self.alias} is not connected")
            return

        self.polling = True
        self.polling_task = asyncio.create_task(self._polling_loop())
        logging.info(f"Started polling for {self.alias}")

    async def stop(self):
        """Stop polling and disconnect"""
        self.polling = False

        # Cancel polling task
        if self.polling_task and not self.polling_task.done():
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass

        # Disconnect BLE
        if self.ble_manager:
            await self.ble_manager.disconnect()

        logging.info(f"Stopped {self.alias}")
        return True

    async def _polling_loop(self):
        """Internal polling loop for device data"""
        try:
            while self.polling and self.ble_manager and self.ble_manager.is_connected:
                try:
                    await self._read_next_section()
                    # Short delay between reads
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logging.error(f"Error in polling loop: {e}")
                    if self.on_error_callback:
                        await self.on_error_callback(self, str(e))

                    # If we lost connection, try to reconnect
                    if not self.ble_manager.is_connected:
                        logging.warning(f"Connection lost to {self.alias}, attempting to reconnect...")
                        success = await self.ble_manager.connect_with_retry(3)
                        if not success:
                            # If reconnect failed, stop polling
                            logging.error(f"Failed to reconnect to {self.alias}, stopping poll")
                            break

                # Sleep between polling cycles
                await asyncio.sleep(POLL_INTERVAL)

            # If we exited the loop because we lost connection, update the state
            if self.polling and (not self.ble_manager or not self.ble_manager.is_connected):
                self.polling = False
                logging.warning(f"Polling stopped for {self.alias} due to connection loss")
        except asyncio.CancelledError:
            # Normal cancellation
            logging.info(f"Polling task cancelled for {self.alias}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in polling loop: {e}")
            self.polling = False

    async def _read_next_section(self):
        """Read the next section from the device"""
        if not self.sections or not self.ble_manager or not self.ble_manager.is_connected:
            return False

        section = self.sections[self.section_index]
        # Create the modbus read command
        dev_id = self.device_id
        fc = 3  # Read function
        register = section['register']
        words = section['words']

        # Calculate the CRC16 for the command
        cmd = [dev_id, fc, register >> 8, register & 0xff, words >> 8, words & 0xff]
        crc = crc16_modbus(bytes(cmd))
        cmd.append(crc[0])
        cmd.append(crc[1])

        # Send the command
        return await self.ble_manager.characteristic_write_value(cmd)
