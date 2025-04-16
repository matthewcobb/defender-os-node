import asyncio
import logging
from .BleManager import BleManager
from .Utils import bytes_to_int, int_to_bytes, crc16_modbus

POLL_INTERVAL = 5

class BaseClient:
    def __init__(self, config):
        self.ble_manager = BleManager(config['mac_address'])
        self.mac_address = config['mac_address']
        self.device_id = config['device_id']
        self.poll_task = None
        self.latest_data = {}
        self.data = {}
        self.sections = []
        self.section_index = 0
        self.connect_lock = asyncio.Lock()
        self.is_connected = False
        self.is_reading = False

    async def connect(self):
        async with self.connect_lock:
            if not self.is_connected:
                try:
                    await self.ble_manager.discover_and_connect()
                    await self.ble_manager.setup_notifications(self.on_data_received)
                    await asyncio.sleep(1) # Give time for connection to settle
                    await self.start_polling()
                    self.is_connected = True
                except Exception as e:
                    logging.error(e)
                    await self.stop_service()

    async def poll_data(self):
        while self.ble_manager.device.is_connected:
            if not self.is_reading:
                await self.read_section()
            await asyncio.sleep(POLL_INTERVAL)
        else:
            await self.stop_service()

    async def start_polling(self):
        self.poll_task = asyncio.create_task(self.poll_data())
        logging.info(f"✅ Polling started for {self.mac_address}")

    async def stop_polling(self):
        # Check if polling was started or not
        if self.poll_task != None:
            self.poll_task.cancel()
            logging.info(f"Polling cancelled for {self.mac_address}")

    async def read_section(self):
        self.is_reading = True
        if not self.sections:
            logging.error("No sections to read")
            return
        section = self.sections[self.section_index]
        logging.debug(f"🤖 Testing section {section['parser']}")
        request = self.create_generic_read_request(self.device_id, 3, section['register'], section['words'])
        success = await self.ble_manager.write_data(request)
        if not success:
            logging.error("Read operation failed.")

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

    # BaseClient handles read operation
    # SubClasses handle write
    async def on_data_received(self, sender, response):
        operation = bytes_to_int(response, 1, 1)

        if operation == 3: # read operation
            logging.debug(f"✅ DATA RECEIVED: Section Index: {self.section_index}")

            if (self.section_index < len(self.sections) and
                self.sections[self.section_index]['parser'] != None and
                self.sections[self.section_index]['words'] * 2 + 5 == len(response)):
                # parse and update data
                try:
                    self.sections[self.section_index]['parser'](response)
                except Exception as e:
                    logging.error(f"Error processing section {self.section_index}: {e}")

            if self.section_index >= len(self.sections) - 1: # last section, read complete
                self.section_index = 0
                self.on_read_operation_complete()
                # Reset the data for the next loop
                self.data = {}
            else:
                self.section_index += 1
                await asyncio.sleep(0.5)
                await self.read_section()
        else:
            logging.warn("on_data_received: unknown operation={}".format(operation))

    def on_read_operation_complete(self):
        logging.debug("on_read_operation_complete!")
        self.latest_data = self.data # Replace the latest data before its reset
        self.is_reading = False # Free up thread
        logging.debug(self.latest_data)

    async def stop_service(self):
        logging.info(f"🤖 Cleaning up {self.mac_address} client...")
        await self.stop_polling()
        # If terminated by another action
        if self.ble_manager.device and self.ble_manager.device.is_connected:
            try:
                await self.ble_manager.disconnect()
            except Exception as e:
                logging.error(e)
        self.is_connected = False
        logging.info(f"👋 {self.mac_address} client closed.")

