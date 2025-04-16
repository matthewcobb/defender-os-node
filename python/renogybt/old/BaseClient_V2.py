import asyncio
import os
import logging
import configparser
import time
from threading import Timer
from .Utils import bytes_to_int, int_to_bytes, crc16_modbus
from .BLE import DeviceManager, Device

ALIAS_PREFIX = 'BT-TH'
NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID = "0000ffd1-0000-1000-8000-00805f9b34fb"
READ_TIMEOUT = 30  # seconds

class BaseClient:
    def __init__(self, config):
        self.config: configparser.ConfigParser = config
        self.manager = None
        self.device = None
        self.poll_timer = None
        self.read_timer = None
        self.data = {}
        self.device_id = self.config['device'].getint('device_id')
        self.sections = []
        self.section_index = 0
        logging.info(f"Init {self.__class__.__name__}: {self.config['device']['alias']} => {self.config['device']['mac_addr']}")

    async def connect(self):
        self.manager = DeviceManager(mac_address=self.config['device']['mac_addr'], alias=self.config['device']['alias'])
        await self.manager.discover()

        if not self.manager.device_found:
            logging.error(f"🛑 - Device not found: {self.config['device']['alias']} => {self.config['device']['mac_addr']}, please check the details provided.")
            self.__stop_service()
        else:
            self.device = Device(
                mac_address=self.manager.device.address,
                notify_uuid=NOTIFY_CHAR_UUID,
                write_uuid=WRITE_CHAR_UUID,
                on_data=self.on_data_received,
                on_resolved=self.__on_resolved,
                on_connect_fail=self.__on_connect_fail
            )
            await self.device.connect()

    async def disconnect(self):
        await self.device.disconnect()
        self.__stop_service()

    def __on_resolved(self):
        logging.info("Resolved services")
        if self.config['data'].getboolean('enable_polling'):
            self.poll_data()
        else:
            self.read_section()

    def on_data_received(self, response):
        if self.read_timer and self.read_timer.is_alive():
            self.read_timer.cancel()
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

    def poll_data(self):
        self.read_section()
        if self.poll_timer and self.poll_timer.is_alive():
            self.poll_timer.cancel()
        self.poll_timer = Timer(self.config['data'].getint('poll_interval'), self.poll_data)
        self.poll_timer.start()

    def read_section(self):
        index = self.section_index
        if self.device_id == None or len(self.sections) == 0:
            return logging.error("base client cannot be used directly")
        request = self.create_generic_read_request(self.device_id, 3, self.sections[index]['register'], self.sections[index]['words'])
        self.device.characteristic_write_value(request)
        self.read_timer = Timer(READ_TIMEOUT, self.on_read_timeout)
        self.read_timer.start()

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

    def __on_error(self, connectFailed=False, error=None):
        logging.error(f"Exception occurred: {error}")
        if connectFailed:
            self.__stop_service()
        else:
            asyncio.run(self.disconnect())

    def __on_connect_fail(self, error):
        logging.error(f"Connection failed: {error}")
        self.__stop_service()

    def __stop_service(self):
        # Clea
        if self.poll_timer and self.poll_timer.is_alive():
            self.poll_timer.cancel()
        if self.read_timer and self.read_timer.is_alive():
            self.read_timer.cancel()

        #exits

