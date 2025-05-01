import asyncio
import configparser
import logging
import traceback
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
        self.client_config = client_config
        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback
        self.ble_manager = None
        self.data = {}
        self.device_id = self.client_config.get('device_id')
        self.alias = self.client_config.get('alias')
        self.mac_addr = self.client_config.get('mac_addr')
        self.sections = []
        self.section_index = 0
        self.polling_task = None
        self.polling = False
        self.last_error = None
        self.read_event = asyncio.Event()
        self.read_lock = asyncio.Lock()
        self.read_future = None
        self.current_timeout = None
        logging.info(f"Initialized {self.__class__.__name__}: {self.alias} => {self.mac_addr}")

    async def start(self):
        """Start the client and connect to the device"""
        try:
            # Create BLE manager
            self.ble_manager = BleManager(
                mac_address=self.mac_addr,
                alias=self.alias,
                on_data=self.on_data_received,
                on_connect_fail=self.on_connect_fail,
                notify_char_uuid=NOTIFY_CHAR_UUID,
                write_char_uuid=WRITE_CHAR_UUID,
                write_service_uuid=WRITE_SERVICE_UUID
            )

            # Discover and connect
            if await self.ble_manager.discover():
                connected = await self.ble_manager.connect()
                if connected:
                    # Start polling
                    await self.start_polling()
                    return True

            # Log error if connection failed
            logging.error(f"Failed to start {self.alias}")
            if self.on_error_callback:
                await self.on_error_callback(self, f"Failed to connect to {self.alias}")
            return False
        except Exception as e:
            logging.error(f"Error starting client: {e}")
            if self.on_error_callback:
                await self.on_error_callback(self, str(e))
            return False

    async def on_connect_fail(self, manager, error):
        """Handle connection failure"""
        self.last_error = error
        logging.error(f"Connection failed: {error}")
        if self.on_error_callback:
            await self.on_error_callback(self, error)

    async def start_polling(self):
        """Start the polling task"""
        if self.polling_task and not self.polling_task.done():
            logging.info(f"Already polling {self.alias}")
            return

        self.polling = True
        self.polling_task = asyncio.create_task(self.polling_loop())
        logging.info(f"Started polling for {self.alias}")

    async def polling_loop(self):
        """Main polling loop"""
        while self.polling:
            try:
                if not await self.ble_manager.ensure_connected():
                    logging.warning(f"Cannot poll {self.alias}: device not connected")
                    await asyncio.sleep(POLL_INTERVAL)
                    continue

                # Reset section index at start of each poll cycle
                self.section_index = 0
                self.data = {}

                # Read all sections
                while self.section_index < len(self.sections) and self.polling:
                    result = await self.read_section()
                    if not result:
                        break

                    # Process read completion if we finished all sections
                    if self.section_index >= len(self.sections):
                        self.data['__device'] = self.alias
                        self.data['__client'] = self.__class__.__name__
                        logging.debug(f"Completed reading all sections for {self.alias}")

                        # Call on_data_callback with complete data
                        if self.on_data_callback:
                            await self.on_data_callback(self, self.data)

                        # Reset for next cycle
                        self.data = {}

                # Wait the polling interval before next cycle
                await asyncio.sleep(POLL_INTERVAL)

            except Exception as e:
                logging.error(f"Error in polling loop for {self.alias}: {e}")
                await asyncio.sleep(POLL_INTERVAL)

    async def read_section(self):
        """Read a section of data from the device"""
        async with self.read_lock:
            if len(self.sections) == 0 or self.device_id is None:
                logging.error(f"Cannot read from {self.alias}: no sections defined")
                return False

            section = self.sections[self.section_index]

            # Create read request
            request = self.create_generic_read_request(
                self.device_id, 3, section['register'], section['words']
            )

            # Setup response handling
            self.read_event.clear()
            self.read_future = asyncio.get_event_loop().create_future()

            # Set timeout
            self.current_timeout = asyncio.create_task(self.handle_timeout())

            # Send request
            if not await self.ble_manager.characteristic_write_value(request):
                if self.current_timeout and not self.current_timeout.done():
                    self.current_timeout.cancel()
                return False

            # Wait for response or timeout
            try:
                await asyncio.wait_for(self.read_future, READ_TIMEOUT)
                return True
            except asyncio.TimeoutError:
                logging.error(f"Timeout reading section {section['register']} from {self.alias}")
                return False
            finally:
                if self.current_timeout and not self.current_timeout.done():
                    self.current_timeout.cancel()

    async def handle_timeout(self):
        """Handle timeout for read operations"""
        await asyncio.sleep(READ_TIMEOUT)
        if not self.read_future.done():
            self.read_future.set_result(False)
            logging.error(f"Read timeout for {self.alias}")
            if self.on_error_callback:
                await self.on_error_callback(self, "Read timeout")

    async def on_data_received(self, response):
        """Process data received from device"""
        if self.current_timeout and not self.current_timeout.done():
            self.current_timeout.cancel()

        operation = bytes_to_int(response, 1, 1)

        if operation == READ_SUCCESS or operation == READ_ERROR:
            if (operation == READ_SUCCESS and
                self.section_index < len(self.sections) and
                self.sections[self.section_index]['parser'] is not None and
                self.sections[self.section_index]['words'] * 2 + 5 == len(response)):

                logging.debug(f"Successful read from {self.alias} section {self.sections[self.section_index]['register']}")

                # Parse the data
                try:
                    self.sections[self.section_index]['parser'](response)
                except Exception as e:
                    logging.error(f"Error parsing data: {e}")

            elif operation == READ_ERROR:
                logging.warning(f"Read operation failed for {self.alias}: {response.hex()}")

            # Move to next section or complete
            self.section_index += 1

            # Complete the future
            if not self.read_future.done():
                self.read_future.set_result(True)

        else:
            logging.warning(f"Unknown operation from {self.alias}: {operation}")
            if not self.read_future.done():
                self.read_future.set_result(False)

    def create_generic_read_request(self, device_id, function, regAddr, readWrd):
        """Create a read request packet"""
        data = []
        data.append(device_id)
        data.append(function)
        data.append(int_to_bytes(regAddr, 0))
        data.append(int_to_bytes(regAddr, 1))
        data.append(int_to_bytes(readWrd, 0))
        data.append(int_to_bytes(readWrd, 1))

        # Add CRC
        crc = crc16_modbus(bytes(data))
        data.append(crc[0])
        data.append(crc[1])

        return data

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

        logging.info(f"Stopped client for {self.alias}")
        return True

    def __on_error(self, error = None):
        logging.error(f"Exception occured: {error}")
        self.__safe_callback(self.on_error_callback, error)
        self.stop()

    def __safe_callback(self, calback, param):
        if calback is not None:
            try:
                calback(self, param)
            except Exception as e:
                logging.error(f"__safe_callback => exception in callback! {e}")
                traceback.print_exc()

    def __safe_parser(self, parser, param):
        if parser is not None:
            try:
                parser(param)
            except Exception as e:
                logging.error(f"exception in parser! {e}")
                traceback.print_exc()
