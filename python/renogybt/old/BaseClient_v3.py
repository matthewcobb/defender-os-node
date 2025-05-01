import asyncio
import logging
import configparser
import time
from bleak import BleakClient, BleakScanner
from .Utils import bytes_to_int, int_to_bytes, crc16_modbus

ALIAS_PREFIX = 'BT-TH'
NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID = "0000ffd1-0000-1000-8000-00805f9b34fb"
DISCOVERY_TIMEOUT = 5 # seconds

class BaseClient:
    def __init__(self, config):
        self.config: configparser.ConfigParser = config
        self.device = None
        self.poll_timer = None
        self.data = {}
        self.device_id = self.config['device'].getint('device_id')
        self.sections = []
        self.section_index = 0
        self.mac_address = self.config['device']['mac_addr']
        logging.info(f"Init {self.__class__.__name__}: {self.config['device']['alias']} => {self.mac_address}")

    async def discover_and_connect(self):
        logging.info(f"🔭 Looking for {self.mac_address}...")
        device = await BleakScanner.find_device_by_address(self.mac_address, timeout=DISCOVERY_TIMEOUT)
        if not device:
            logging.error(f"🛑 - Device not found: {self.mac_address}, please check the configuration.")
            return

        self.device = BleakClient(device)
        try:
            await self.device.connect()
            logging.info(f"Connected to {self.mac_address}")
            await self.services_resolved()
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            self.on_connect_fail(e)

    async def disconnect(self):
        if self.device and self.device.is_connected:
            await self.device.disconnect()
            logging.info(f"Disconnected from {self.mac_address}")
        self.stop_service()

    async def services_resolved(self):
        for service in self.device.services:
            for characteristic in service.characteristics:
                if characteristic.uuid == NOTIFY_CHAR_UUID:
                    await self.device.start_notify(characteristic.uuid, self.on_data_received)
                    logging.info(f"Subscribed to notification {characteristic.uuid}")
                if characteristic.uuid == WRITE_CHAR_UUID:
                    self.write_characteristic = characteristic
                    logging.info(f"Found write characteristic {characteristic.uuid}")

        self.on_resolved()

    async def on_resolved(self):
        logging.info("Resolved services")
        if self.config['data'].getboolean('enable_polling'):
            self.poll_data()
        else:
            self.read_section()

    async def poll_data(self):
        while True:
            await self.read_section()
            if self.poll_timer and self.poll_timer.is_alive():
                self.poll_timer.cancel()
            # Schedule the next poll after READ_TIMEOUT seconds
            # asyncio.sleep is non-blocking and cooperates with the asyncio event loop
            await asyncio.sleep(self.config['data'].getint('poll_interval'))

    async def read_section(self):
        index = self.section_index
        if self.device_id is None or len(self.sections) == 0:
            return logging.error("Base client cannot be used directly")
        request = self.create_generic_read_request(self.device_id, 3, self.sections[index]['register'], self.sections[index]['words'])

        try:
            await self.device.write_gatt_char(WRITE_CHAR_UUID, request)
            logging.info("Write request sent.")
        except Exception as e:
            self.on_read_timeout(self)
            logging.error(f"Failed to write characteristic: {e}")

    def create_generic_read_request(self, device_id, function, regAddr, readWrd):
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
            logging.debug("{} {} => {}".format("create_request_payload", regAddr, data))
        return data

    def on_data_received(self, response):
        operation = bytes_to_int(response, 1, 1)

        if operation == 3: # read operation
            logging.info("on_data_received: response for read operation")
            if (self.section_index < len(self.sections) and
                self.sections[self.section_index]['parser'] != None and
                self.sections[self.section_index]['words'] * 2 + 5 == len(response)):
                # parse and update data
                self.sections[self.section_index]['parser'](response)

            if self.section_index >= len(self.sections) - 1: # last section, read complete
                self.section_index = 0
                self.on_read_operation_complete()
                self.data = {}
            else:
                self.section_index += 1
                time.sleep(0.5)
                self.read_section()
        else:
            logging.warn("on_data_received: unknown operation={}".format(operation))

    def on_read_operation_complete(self):
        logging.info("on_read_operation_complete")
        self.data['__device'] = self.config['device']['alias']
        self.data['__client'] = self.__class__.__name__
        if self.on_data_callback is not None:
            self.on_data_callback(self, self.data)

    def on_read_timeout(self):
        logging.error("on_read_timeout => please check your device_id!")
        asyncio.run(self.disconnect())

    def on_connect_fail(self, error):
        logging.error(f"Connection failed: {error}")
        self.stop_service()

    def stop_service(self):
        # Cleanup
        if self.poll_timer and self.poll_timer.is_alive():
            self.poll_timer.cancel()
        #exits

