import asyncio
import logging
from bleak import BleakClient, BleakScanner, BLEDevice

DISCOVERY_TIMEOUT = 10  # max wait time to complete the bluetooth scanning (seconds)

class BleManager:
    def __init__(self, mac_address, alias, on_data, on_connect_fail, write_service_uuid, notify_char_uuid, write_char_uuid):
        self.mac_address = mac_address
        self.device_alias = alias
        self.data_callback = on_data
        self.connect_fail_callback = on_connect_fail
        self.write_service_uuid = write_service_uuid
        self.notify_char_uuid = notify_char_uuid
        self.write_char_uuid = write_char_uuid
        self.write_char_handle = None
        self.device = None
        self.client = None
        self.discovered_devices = []
        self.is_connected = False
        self.connection_lock = asyncio.Lock()

    async def discover(self):
        """Discover device with BleakScanner"""
        mac_address = self.mac_address.upper()
        logging.info(f"Starting discovery for {self.device_alias}...")

        try:
            self.discovered_devices = await BleakScanner.discover(timeout=DISCOVERY_TIMEOUT)
            logging.info(f"Devices found: {len(self.discovered_devices)}")

            for dev in self.discovered_devices:
                if dev.address and (dev.address.upper() == mac_address or (dev.name and dev.name.strip() == self.device_alias)):
                    logging.info(f"Found matching device {dev.name} => {dev.address}")
                    self.device = dev
                    return True

            # Log potential devices if target not found
            for dev in self.discovered_devices:
                if dev.name and any(dev.name.startswith(prefix) for prefix in ['BT-TH', 'RNGRBP', 'BTRIC']):
                    logging.info(f"Possible device found! ====> {dev.name} > [{dev.address}]")

            return False
        except Exception as e:
            logging.error(f"Error during discovery: {e}")
            return False

    async def connect(self):
        """Connect to device with connection lock to prevent multiple connections"""
        if not self.device:
            logging.error("No device to connect to!")
            return False

        # Use lock to prevent multiple simultaneous connection attempts
        async with self.connection_lock:
            if self.is_connected:
                return True

            try:
                self.client = BleakClient(self.device)
                await self.client.connect()

                if not self.client.is_connected:
                    logging.error("Failed to connect")
                    return False

                logging.info(f"✅ Connected to {self.device_alias}")
                self.is_connected = True

                # Setup notifications and find write characteristic
                for service in self.client.services:
                    for characteristic in service.characteristics:
                        if characteristic.uuid == self.notify_char_uuid:
                            await self.client.start_notify(characteristic, self.notification_callback)
                            logging.info(f"Subscribed to notification {characteristic.uuid}")
                        if characteristic.uuid == self.write_char_uuid and service.uuid == self.write_service_uuid:
                            self.write_char_handle = characteristic.handle
                            logging.info(f"Found write characteristic {characteristic.uuid}")

                return True

            except Exception as e:
                logging.error(f"Error connecting to device: {e}")
                if self.connect_fail_callback:
                    await self.connect_fail_callback(self, str(e))
                return False

    async def notification_callback(self, characteristic, data: bytearray):
        """Handle incoming notifications from BLE device"""
        if self.data_callback:
            await self.data_callback(data)

    async def characteristic_write_value(self, data):
        """Write data to characteristic with retry logic"""
        if not self.is_connected:
            logging.warning("Cannot write: device not connected")
            await self.connect()
            if not self.is_connected:
                return False

        try:
            await self.client.write_gatt_char(self.write_char_handle, bytearray(data), response=False)
            return True
        except Exception as e:
            logging.error(f"Write failed: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Disconnect from device"""
        if self.client and self.client.is_connected:
            try:
                logging.info(f"Disconnecting device: {self.device_alias}")
                await self.client.disconnect()
                self.is_connected = False
                return True
            except Exception as e:
                logging.error(f"Error disconnecting: {e}")
                return False
        return True

    async def ensure_connected(self):
        """Ensure device is connected, reconnect if needed"""
        if not self.is_connected and self.device:
            return await self.connect()
        elif not self.device:
            if await self.discover():
                return await self.connect()
            return False
        return True
