import asyncio
import logging
import sys
import platform
from bleak import BleakClient, BleakScanner, BLEDevice

DISCOVERY_TIMEOUT = 5 # max wait time to complete the bluetooth scanning (seconds)

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
        self.device: BLEDevice = None
        self.client: BleakClient = None
        self.discovered_devices = []
        # Log platform info for debugging
        logging.info(f"📱 Platform: {platform.system()} {platform.release()} {platform.machine()}")
        logging.info(f"📱 Python: {platform.python_version()}")

    async def discover(self):
        mac_address = self.mac_address.upper()
        logging.info(f"🔍 Starting discovery for device: {self.device_alias} ({mac_address})...")
        try:
            self.discovered_devices = await BleakScanner.discover(timeout=DISCOVERY_TIMEOUT)
            logging.info("📊 Devices found: %s", len(self.discovered_devices))
            for dev in self.discovered_devices:
                logging.info(f"📱 Device: {dev.name or 'Unknown'} ({dev.address})")
                if dev.metadata:
                    logging.info(f"   Metadata: {dev.metadata}")

            device_found = False
            for dev in self.discovered_devices:
                if dev.address != None and (dev.address.upper() == mac_address or (dev.name and dev.name.strip() == self.device_alias)):
                    logging.info(f"🔌 Found matching device {dev.name} => {dev.address}")
                    self.device = dev
                    device_found = True

            if not device_found:
                logging.error(f"❌ Device {self.device_alias} ({mac_address}) not found in scan results")
                # Log nearby Bluetooth devices with similar prefixes that might be relevant
                for dev in self.discovered_devices:
                    if dev.name and any(dev.name.startswith(prefix) for prefix in ['BT-TH', 'RNGRBP', 'BTRIC']):
                        logging.info(f"🔍 Possible Renogy device: {dev.name} => {dev.address}")
        except Exception as e:
            logging.error(f"❌ Error during discovery: {e}")
            logging.exception("Discovery exception details:")

    async def connect(self):
        if not self.device:
            logging.error("❌ No device connected!")
            return False

        disconnect_handler = self._create_disconnect_handler()

        self.client = BleakClient(self.device, disconnected_callback=disconnect_handler)
        try:
            logging.info(f"🔌 Connecting to {self.device.name or 'Unknown'} ({self.device.address})...")
            await self.client.connect()
            logging.info(f"🔌 Client connection status: {self.client.is_connected}")

            if not self.client.is_connected:
                logging.error("❌ Unable to connect")
                return False

            # Log MTU size if available
            try:
                mtu = await self.client.get_mtu()
                logging.info(f"📊 Connection MTU: {mtu}")
            except:
                logging.info("📊 Could not retrieve MTU size")

            logging.info("🔍 Scanning for services and characteristics...")

            notify_char_found = False
            write_char_found = False

            for service in self.client.services:
                logging.info(f"   Service: {service.uuid}")
                for characteristic in service.characteristics:
                    props = []
                    if characteristic.properties:
                        if "read" in characteristic.properties:
                            props.append("read")
                        if "write" in characteristic.properties:
                            props.append("write")
                        if "notify" in characteristic.properties:
                            props.append("notify")
                    logging.info(f"      Char: {characteristic.uuid} ({', '.join(props)})")

                    if characteristic.uuid == self.notify_char_uuid:
                        await self.client.start_notify(characteristic, self.notification_callback)
                        logging.info(f"🔔 Subscribed to notifications on {characteristic.uuid}")
                        notify_char_found = True

                    if characteristic.uuid == self.write_char_uuid and service.uuid == self.write_service_uuid:
                        self.write_char_handle = characteristic.handle
                        logging.info(f"✏️ Found write characteristic {characteristic.uuid}, service {service.uuid}, handle {characteristic.handle}")
                        write_char_found = True

            if not notify_char_found:
                logging.error(f"❌ Notification characteristic {self.notify_char_uuid} not found!")

            if not write_char_found:
                logging.error(f"❌ Write characteristic {self.write_char_uuid} not found!")

            return True

        except Exception as e:
            logging.error(f"❌ Error connecting to device: {e}")
            logging.exception("Connection exception details:")
            self.connect_fail_callback(sys.exc_info())
            return False

    def _create_disconnect_handler(self):
        """Creates a handler for disconnect events"""
        async def on_disconnect(client):
            device_info = f"{self.device.name or 'Unknown'} ({self.device.address})"
            logging.error(f"❌ Device disconnected: {device_info}")
            # Log attempt to reconnect for informational purposes - actual reconnect happens in BaseClient
            logging.info(f"ℹ️ Reconnection will be handled during next polling interval")
        return on_disconnect

    async def notification_callback(self, characteristic, data: bytearray):
        logging.info(f"📊 Notification received from {characteristic.uuid}: {len(data)} bytes")
        try:
            await self.data_callback(data)
        except Exception as e:
            logging.error(f"❌ Error in notification callback: {e}")
            logging.exception("Notification callback exception details:")

    async def characteristic_write_value(self, data):
        try:
            if not self.client or not self.client.is_connected:
                logging.error("❌ Cannot write: client not connected")
                return

            logging.info(f'📊 Writing to {self.write_char_uuid} ({len(data)} bytes): {data}')
            retry_count = 0
            max_retries = 3

            while retry_count < max_retries:
                try:
                    await self.client.write_gatt_char(self.write_char_handle, bytearray(data), response=False)
                    logging.info('✅ Write operation succeeded')
                    # Success - exit retry loop
                    break
                except Exception as write_error:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise write_error
                    logging.warning(f'⚠️ Write retry {retry_count}/{max_retries}: {write_error}')
                    # Add short delay between retries
                    await asyncio.sleep(0.5)

            # Add slightly longer delay after successful write to ensure device has time to process
            await asyncio.sleep(1.0)
        except Exception as e:
            logging.error(f'❌ Write operation failed: {e}')
            logging.exception("Write operation exception details:")
            raise e

    async def disconnect(self):
        if self.client and self.client.is_connected:
            try:
                logging.info(f"🔌 Disconnecting device: {self.device.name or 'Unknown'} ({self.device.address})")
                await self.client.disconnect()
                logging.info(f"✅ Device successfully disconnected")
            except Exception as e:
                logging.error(f"❌ Error disconnecting device: {e}")
                logging.exception("Disconnect exception details:")
