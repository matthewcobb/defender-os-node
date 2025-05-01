import asyncio
import logging
import traceback
from .BleManager import BleManager
from .Utils import bytes_to_int, crc16_modbus, int_to_bytes

# Base class that works with all Renogy family devices
# Should be extended by each client with its own parsers and section definitions

ALIAS_PREFIXES = ['BT-TH', 'RNGRBP', 'BTRIC']
WRITE_SERVICE_UUID = "0000ffd0-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID  = "0000ffd1-0000-1000-8000-00805f9b34fb"
READ_TIMEOUT = 15 # (seconds)
READ_SUCCESS = 3
READ_ERROR = 131

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
        logging.info(f"🚀 Init {self.__class__.__name__}: {self.client_config.get('alias')} => {self.client_config.get('mac_addr')}")

    async def connect(self):
        """Connect to the BLE device"""
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
            logging.error(f"🔴 Device not found: {self.client_config.get('alias')} => {self.client_config.get('mac_addr')}, please check the details provided.")
            for dev in self.ble_manager.discovered_devices:
                if dev.name != None and dev.name.startswith(tuple(ALIAS_PREFIXES)):
                    logging.info(f"🟢 Possible device found! ====> {dev.name} > [{dev.address}]")
            await self.disconnect()
            return False
        else:
            await self.ble_manager.connect()
            self.connected = self.ble_manager.client and self.ble_manager.client.is_connected
            return self.connected

    async def disconnect(self):
        """Disconnect from the BLE device"""
        self.connected = False
        if self.read_timeout and not self.read_timeout.cancelled():
            self.read_timeout.cancel()
        if self.ble_manager:
            await self.ble_manager.disconnect()

    async def on_data_received(self, response):
        """Handle data received from the device"""
        if self.read_timeout and not self.read_timeout.cancelled():
            self.read_timeout.cancel()

        operation = bytes_to_int(response, 1, 1)

        if operation == READ_SUCCESS or operation == READ_ERROR:
            if (operation == READ_SUCCESS and
                self.section_index < len(self.sections) and
                self.sections[self.section_index]['parser'] != None and
                self.sections[self.section_index]['words'] * 2 + 5 == len(response)):
                # call the parser and update data
                logging.info(f"🟢 on_data_received: read operation success")
                self.__safe_parser(self.sections[self.section_index]['parser'], response)
            else:
                logging.info(f"🔴 on_data_received: read operation failed: {response.hex()}")

            if self.section_index >= len(self.sections) - 1:  # last section, read complete
                self.section_index = 0
                self.on_read_operation_complete()
                self.data = {}
            else:
                self.section_index += 1
                await asyncio.sleep(0.1)
                await self.read_section()
        else:
            logging.warning(f"🟡 on_data_received: unknown operation={operation}")

    def on_read_operation_complete(self):
        """Called when all sections have been read"""
        logging.info("🟢 on_read_operation_complete")
        self.data['__device'] = self.client_config.get('alias')
        self.data['__client'] = self.__class__.__name__
        self.__safe_callback(self.on_data_callback, self.data)

    def on_read_timeout(self):
        """Called when a read operation times out"""
        logging.error("🔴 on_read_timeout => Timed out! Please check your device_id!")

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
            logging.error("🔴 Cannot read section: Device not connected")
            return

        index = self.section_index
        if self.device_id == None or len(self.sections) == 0:
            return logging.error("🔴 BaseClient cannot be used directly")

        loop = asyncio.get_event_loop()
        self.read_timeout = loop.call_later(READ_TIMEOUT, self.on_read_timeout)
        request = self.create_generic_read_request(self.device_id, 3, self.sections[index]['register'], self.sections[index]['words'])
        await self.ble_manager.characteristic_write_value(request)

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
        logging.error(f"🔴 Exception occurred: {error}")
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
