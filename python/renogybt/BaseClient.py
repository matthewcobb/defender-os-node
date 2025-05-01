import asyncio
import logging
import traceback
from .BleManager import BleManager
from .Utils import bytes_to_int, crc16_modbus, int_to_bytes
import platform

# Base class that works with all Renogy family devices
# Should be extended by each client with its own parsers and section definitions

ALIAS_PREFIXES = ['BT-TH', 'RNGRBP', 'BTRIC']
WRITE_SERVICE_UUID = "0000ffd0-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID  = "0000ffd1-0000-1000-8000-00805f9b34fb"

# Set timeout based on platform - Raspberry Pi needs longer timeouts
if platform.machine().startswith('arm') or platform.system() == 'Linux':
    READ_TIMEOUT = 45  # Increased timeout for Raspberry Pi / Linux
else:
    READ_TIMEOUT = 15  # Default timeout for Mac/Windows

READ_SUCCESS = 3
READ_ERROR = 131

# Add system-level logging to help diagnose issues
import os
import time

class BaseClient:
    def __init__(self, client_config, on_data_callback=None, on_error_callback=None):
        self.client_config = client_config
        self.ble_manager = None
        self.device = None
        self.read_timeout = None
        self.data = {}
        self.device_id = self.client_config.get('device_id', 255)
        self.sections = []
        self.section_index = 0
        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback
        self.connected = False
        self.connect_time = None
        self.last_read_time = None
        self.read_count = 0
        self.connection_attempts = 0
        self.timeout_count = 0

        logging.info(f"🚀 Initializing {self.__class__.__name__} for {self.client_config.get('alias')} => {self.client_config.get('mac_addr')}")
        self._log_system_info()

    def _log_system_info(self):
        """Log system information that might be relevant to Bluetooth issues"""
        try:
            uname = platform.uname()
            logging.info(f"System: {uname.system} {uname.release} {uname.version}")
            logging.info(f"Machine: {uname.machine}")

            # On Linux, try to get Bluetooth adapter info
            if platform.system() == "Linux":
                try:
                    import subprocess
                    result = subprocess.run(['hciconfig'], capture_output=True, text=True)
                    if result.returncode == 0:
                        logging.info(f"Bluetooth adapters:\n{result.stdout.strip()}")
                    else:
                        logging.warning(f"Could not get Bluetooth adapter info: {result.stderr}")
                except Exception as e:
                    logging.warning(f"Error getting Bluetooth adapter info: {e}")
        except Exception as e:
            logging.warning(f"Could not log system info: {e}")

    async def connect(self):
        """Connect to the BLE device"""
        self.connection_attempts += 1
        logging.info(f"🔌 Connection attempt #{self.connection_attempts} to {self.client_config.get('alias')}")

        self.ble_manager = BleManager(
            mac_address=self.client_config.get('mac_addr'),
            alias=self.client_config.get('alias'),
            on_data=self.on_data_received,
            on_connect_fail=self.__on_connect_fail,
            notify_char_uuid=NOTIFY_CHAR_UUID,
            write_char_uuid=WRITE_CHAR_UUID,
            write_service_uuid=WRITE_SERVICE_UUID
        )

        await self.ble_manager.discover()

        if not self.ble_manager.device:
            logging.error(f"❌ Device not found: {self.client_config.get('alias')} => {self.client_config.get('mac_addr')}")
            for dev in self.ble_manager.discovered_devices:
                if dev.name != None and dev.name.startswith(tuple(ALIAS_PREFIXES)):
                    logging.info(f"🔍 Possible device found! ====> {dev.name} > [{dev.address}]")
            await self.disconnect()
            return False
        else:
            connected = await self.ble_manager.connect()
            self.connected = connected and self.ble_manager.client and self.ble_manager.client.is_connected

            if self.connected:
                self.connect_time = time.time()
                logging.info(f"✅ Successfully connected to {self.client_config.get('alias')} at {time.strftime('%H:%M:%S')}")
            else:
                logging.error(f"❌ Failed to establish connection to {self.client_config.get('alias')}")

            return self.connected

    async def disconnect(self):
        """Disconnect from the BLE device"""
        if self.connected:
            logging.info(f"🔌 Disconnecting from {self.client_config.get('alias')}")
            connection_duration = 0
            if self.connect_time:
                connection_duration = time.time() - self.connect_time
                logging.info(f"📊 Connection duration: {connection_duration:.1f} seconds")

            if self.read_count > 0:
                logging.info(f"📊 Successfully completed {self.read_count} read operations")

        self.connected = False
        if self.read_timeout and not self.read_timeout.cancelled():
            self.read_timeout.cancel()
            logging.info("⏱️ Cancelled pending read timeout")

        if self.ble_manager:
            await self.ble_manager.disconnect()

    async def on_data_received(self, response):
        """Handle data received from the device"""
        self.last_read_time = time.time()

        if self.read_timeout and not self.read_timeout.cancelled():
            self.read_timeout.cancel()
            logging.info("⏱️ Cancelled read timeout after receiving data")

        operation = bytes_to_int(response, 1, 1)
        response_hex = response.hex()[:20] + "..." if len(response) > 10 else response.hex()
        logging.info(f"📊 Received data: operation={operation}, length={len(response)}, data={response_hex}")

        if operation == READ_SUCCESS or operation == READ_ERROR:
            if (operation == READ_SUCCESS and
                self.section_index < len(self.sections) and
                self.sections[self.section_index]['parser'] != None and
                self.sections[self.section_index]['words'] * 2 + 5 == len(response)):
                # call the parser and update data
                logging.info(f"✅ Read operation successful for section {self.section_index}")
                self.read_count += 1
                self.__safe_parser(self.sections[self.section_index]['parser'], response)
            else:
                logging.error(f"❌ Read operation failed: {response.hex()}")

            if self.section_index >= len(self.sections) - 1:  # last section, read complete
                logging.info(f"✅ All sections read successfully ({len(self.sections)} sections)")
                self.section_index = 0
                self.on_read_operation_complete()
                self.data = {}
            else:
                self.section_index += 1
                await asyncio.sleep(0.1)
                await self.read_section()
        else:
            logging.warning(f"⚠️ Unknown operation received: {operation}")

    def on_read_operation_complete(self):
        """Called when all sections have been read"""
        logging.info("🟢 on_read_operation_complete")
        self.data['__device'] = self.client_config.get('alias')
        self.data['__client'] = self.__class__.__name__
        self.__safe_callback(self.on_data_callback, self.data)

    def on_read_timeout(self):
        """Called when a read operation times out"""
        self.timeout_count += 1
        current_time = time.time()

        if self.last_read_time:
            time_since_last_read = current_time - self.last_read_time
            logging.error(f"⏱️ Timeout #{self.timeout_count} after {time_since_last_read:.1f} seconds since last successful read")
        else:
            connection_duration = 0
            if self.connect_time:
                connection_duration = current_time - self.connect_time
            logging.error(f"⏱️ Timeout #{self.timeout_count} after {connection_duration:.1f} seconds since connection")

        logging.error(f"❌ Read timeout for {self.client_config.get('alias')} on section {self.section_index}. Please check your device_id!")

        # Cancel the current timeout if it exists
        if self.read_timeout and not self.read_timeout.cancelled():
            self.read_timeout.cancel()

        # Mark as disconnected so next read will trigger reconnection
        self.connected = False

        # Notify about the error but don't stop the monitoring
        self.__safe_callback(self.on_error_callback, "Read timeout")

        # Reset section index to start fresh on reconnect
        self.section_index = 0

    async def read_section(self):
        """Read a section of data from the device"""
        if not self.connected:
            logging.error(f"❌ Cannot read section: Device {self.client_config.get('alias')} not connected")
            return

        index = self.section_index
        if self.device_id == None or len(self.sections) == 0:
            return logging.error("❌ BaseClient cannot be used directly")

        section_info = f"register={self.sections[index]['register']}, words={self.sections[index]['words']}"
        logging.info(f"📊 Reading section {index}/{len(self.sections)-1} from {self.client_config.get('alias')}: {section_info}")

        loop = asyncio.get_event_loop()
        self.read_timeout = loop.call_later(READ_TIMEOUT, self.on_read_timeout)
        logging.info(f"⏱️ Set read timeout of {READ_TIMEOUT} seconds")

        request = self.create_generic_read_request(self.device_id, 3, self.sections[index]['register'], self.sections[index]['words'])
        try:
            await self.ble_manager.characteristic_write_value(request)
        except Exception as e:
            logging.error(f"❌ Error writing to characteristic: {e}")
            # Cancel the timeout since we know the write failed
            if self.read_timeout and not self.read_timeout.cancelled():
                self.read_timeout.cancel()
            raise e

    async def read_all_data(self):
        """Read all sections of data from the device"""
        if not self.connected:
            logging.warning(f"🟡 Device {self.client_config.get('alias')} not connected, attempting to connect")
            connected = await self.connect()
            if not connected:
                logging.error(f"🔴 Failed to connect to {self.client_config.get('alias')}")
                # Attempt to completely clean up and reconnect on failure
                await self.disconnect()
                # Add a short delay before retry
                await asyncio.sleep(1)
                # Try one more time
                connected = await self.connect()
                if not connected:
                    logging.error(f"🔴 Second attempt to connect to {self.client_config.get('alias')} failed")
                    return False

        self.section_index = 0
        self.data = {}
        try:
            await self.read_section()
            return True
        except Exception as e:
            logging.error(f"🔴 Exception in read_all_data: {e}")
            # Mark as disconnected so next poll will attempt reconnection
            self.connected = False
            return False

    def create_generic_read_request(self, device_id, function, regAddr, readWrd):
        """Create a generic read request"""
        data = None
        if regAddr != None and readWrd != None:
            data = []
            data.append(device_id)
            data.append(function)
            data.append(int_to_bytes(regAddr, 0))
            data.append(int_to_bytes(regAddr, 1))
            data.append(int_to_bytes(readWrd, 0))
            data.append(int_to_bytes(readWrd, 1))

            crc = crc16_modbus(bytes(data))
            data.append(crc[0])
            data.append(crc[1])
            logging.debug("🔍 {} {} => {}".format("create_request_payload", regAddr, data))
        return data

    def __on_error(self, error = None):
        """Handle errors"""
        logging.error(f"❌ Exception occurred: {error}")
        self.__safe_callback(self.on_error_callback, error)

    def __on_connect_fail(self, error):
        """Handle connection failures"""
        logging.error(f"🔴 Connection failed: {error}")
        self.__safe_callback(self.on_error_callback, error)

    def __safe_callback(self, callback, param):
        """Safely call a callback function"""
        if callback is not None:
            try:
                callback(self, param)
            except Exception as e:
                logging.error(f"🔴 __safe_callback => exception in callback! {e}")
                traceback.print_exc()

    def __safe_parser(self, parser, param):
        """Safely call a parser function"""
        if parser is not None:
            try:
                parser(param)
            except Exception as e:
                logging.error(f"🔴 exception in parser! {e}")
                traceback.print_exc()
