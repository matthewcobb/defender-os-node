import asyncio
import logging
from bleak import BleakScanner, BleakClient

DISCOVERY_TIMEOUT = 5  # max wait time to complete the bluetooth scanning (seconds)

class DeviceManager:
    def __init__(self, mac_address, alias):
        self.device_found = False
        self.mac_address = mac_address.upper()
        self.device_alias = alias
        self.device = None

    async def discover(self):
        logging.info(f"🔭 Looking for {self.device_alias}...")
        devices = await BleakScanner.discover(timeout=DISCOVERY_TIMEOUT)
        print("\n----------- AVAILABLE DEVICES -----------")
        for device in devices:
            print(device)
            if device.address.upper() == self.mac_address or (device.name and device.name.strip() == self.device_alias):
                logging.info(f"Found matching device {device.name} => [{device.address}]")
                self.device_found = True
                self.device = device
                break
        # if not self.device_found:
        #     logging.error(f"{self.device_alias} not found, please check the details provided.")
class Device:
    def __init__(self, mac_address, notify_uuid, write_uuid, on_data, on_resolved, on_connect_fail):
        self.mac_address = mac_address
        self.notify_char_uuid = notify_uuid
        self.write_char_uuid = write_uuid
        self.client = BleakClient(mac_address)
        self.data_callback = on_data
        self.resolved_callback = on_resolved
        self.connect_fail_callback = on_connect_fail

    async def connect(self):
        try:
            await self.client.connect()
            logging.info(f"[{self.mac_address}] Connected")
            self.client.set_disconnected_callback(self.on_disconnect)
            await self.services_resolved()
        except Exception as e:
            logging.error(f"[{self.mac_address}] Connection failed: {e}")
            self.connect_fail_callback(e)

    async def disconnect(self):
        await self.client.disconnect()
        logging.info(f"[{self.mac_address}] Disconnected")

    async def services_resolved(self):
        for service in self.client.services:
            for characteristic in service.characteristics:
                if characteristic.uuid == self.notify_char_uuid:
                    await self.client.start_notify(characteristic.uuid, self.notification_handler)
                    logging.info(f"Subscribed to notification {characteristic.uuid}")
                if characteristic.uuid == self.write_char_uuid:
                    self.write_characteristic = characteristic
                    logging.info(f"Found write characteristic {characteristic.uuid}")

        self.resolved_callback()

    async def write_value(self, value):
        await self.client.write_gatt_char(self.write_characteristic, value)
        logging.info('Characteristic write value succeeded')

    def notification_handler(self, sender, data):
        logging.info('Notification received from: {0}: {1}'.format(sender, data))
        self.data_callback(data)

    def on_disconnect(self, client):
        logging.info(f"[{client.address}] Disconnected callback called!")
        self.connect_fail_callback('Disconnected')

# Usage Example:
# async def main():
#     manager = DeviceManager("MAC_ADDRESS_HERE", "DEVICE_ALIAS_HERE")
#     await manager.discover()
#     if manager.device_found:
#         device = Device(manager.device.address, "NOTIFY_UUID_HERE", "WRITE_UUID_HERE", on_data_callback, on_resolved_callback, on_connect_fail_callback)
#         await device.connect()
#         # Perform operations with the device
#         await device.disconnect()
#
# asyncio.run(main())
