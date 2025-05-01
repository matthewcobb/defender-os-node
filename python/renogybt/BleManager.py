import asyncio
import logging
from bleak import BleakClient, BleakScanner, BLEDevice

DISCOVERY_TIMEOUT = 10  # max wait time to complete the bluetooth scanning (seconds)
MAX_RETRIES = 5  # Maximum number of connection attempts before giving up

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
        self.is_connected = False

    async def discover(self):
        """Discover device with BleakScanner"""
        mac_address = self.mac_address.upper()
        logging.info(f"Starting discovery for {self.device_alias}...")

        try:
            self.discovered_devices = await BleakScanner.discover(timeout=DISCOVERY_TIMEOUT)

            for dev in self.discovered_devices:
                if dev.address and (dev.address.upper() == mac_address or (dev.name and dev.name.strip() == self.device_alias)):
                    logging.info(f"Found matching device {dev.name} => {dev.address}")
                    self.device = dev
                    return True

            logging.warning(f"Device not found: {self.device_alias}")
            return False
        except Exception as e:
            logging.error(f"Error during discovery: {e}")
            return False

    async def connect_with_retry(self, max_attempts=MAX_RETRIES):
        """Connect to device with retries

        Args:
            max_attempts: Maximum number of connection attempts (0 = infinite)

        Returns:
            bool: True if successfully connected
        """
        if self.is_connected and self.client and self.client.is_connected:
            return True

        attempts = 0
        retry_interval = 5  # Start with 5 seconds between retries

        while max_attempts == 0 or attempts < max_attempts:
            # Try discovery if needed
            if not self.device and not await self.discover():
                attempts += 1
                logging.warning(f"🔍 Discovery failed, retrying in {retry_interval}s (attempt {attempts}/{max_attempts})")
                await asyncio.sleep(retry_interval)
                retry_interval = min(retry_interval * 1.5, 30)
                continue

            # Try to connect
            try:
                logging.info(f"🔌 Connecting to {self.device_alias}...")

                # Cleanup any previous client
                if self.client:
                    try:
                        await self.client.disconnect()
                    except:
                        pass

                self.client = BleakClient(self.device)
                await self.client.connect()

                if not self.client.is_connected:
                    logging.warning(f"❌ Connection to {self.device_alias} failed")
                    attempts += 1
                    await asyncio.sleep(retry_interval)
                    retry_interval = min(retry_interval * 1.5, 30)
                    continue

                # Connected successfully
                logging.info(f"✅ Connected to {self.device_alias}")

                # Ensure service discovery is complete
                # This is critical on Raspberry Pi to prevent 'Service Discovery not performed' errors
                await asyncio.sleep(1)  # Small delay to ensure service discovery completes

                # Setup notifications and find write characteristic
                self.is_connected = True
                service_discovery_complete = False

                for service in self.client.services:
                    for characteristic in service.characteristics:
                        if characteristic.uuid == self.notify_char_uuid:
                            await self.client.start_notify(characteristic, self.notification_callback)
                            logging.info(f"📡 Subscribed to notification {characteristic.uuid}")
                        if characteristic.uuid == self.write_char_uuid and service.uuid == self.write_service_uuid:
                            self.write_char_handle = characteristic.handle
                            service_discovery_complete = True
                            logging.info(f"📝 Found write characteristic {characteristic.uuid}")

                # Verify that service discovery succeeded
                if not service_discovery_complete:
                    logging.error(f"⚠️ Service discovery failed - could not find write characteristic")
                    self.is_connected = False
                    attempts += 1
                    await asyncio.sleep(retry_interval)
                    retry_interval = min(retry_interval * 1.5, 30)
                    continue

                return True

            except Exception as e:
                logging.error(f"❌ Error connecting to {self.device_alias}: {e}")
                if self.connect_fail_callback:
                    await self.connect_fail_callback(self, str(e))

                attempts += 1
                logging.warning(f"🔄 Connection attempt {attempts}/{max_attempts} failed, retrying in {retry_interval}s")
                await asyncio.sleep(retry_interval)
                retry_interval = min(retry_interval * 1.5, 30)

        logging.error(f"❌ Failed to connect to {self.device_alias} after {attempts} attempts")
        return False

    async def ensure_connected(self):
        """Ensure the device is connected and service discovery is complete"""
        if not self.is_connected or not self.client or not self.client.is_connected:
            logging.warning(f"📵 Device {self.device_alias} not connected, attempting to reconnect")
            return await self.connect_with_retry(3)

        # Check if service discovery is complete
        if self.write_char_handle is None:
            logging.warning(f"⚠️ Service discovery not complete for {self.device_alias}, attempting to reconnect")
            await self.disconnect()  # Disconnect first
            return await self.connect_with_retry(3)

        return True

    async def notification_callback(self, characteristic, data: bytearray):
        """Handle incoming notifications from BLE device"""
        if self.data_callback:
            await self.data_callback(data)

    async def characteristic_write_value(self, data):
        """Write data to characteristic"""
        if not self.is_connected:
            logging.warning(f"📵 Cannot write to {self.device_alias}: not connected")
            return False

        # Verify write characteristic is available
        if self.write_char_handle is None:
            logging.error(f"⚠️ Cannot write to {self.device_alias}: Service Discovery not complete")
            # Try to reconnect rather than immediately failing
            if not await self.ensure_connected():
                self.is_connected = False
                return False

        # Maximum retry attempts for writing
        max_retries = 2
        retry_count = 0

        while retry_count <= max_retries:
            try:
                await self.client.write_gatt_char(self.write_char_handle, bytearray(data), response=False)
                return True
            except Exception as e:
                retry_count += 1
                error_msg = str(e)

                # Check for service discovery error specifically
                if "Service Discovery" in error_msg:
                    logging.warning(f"⚙️ Service discovery error, attempt {retry_count}/{max_retries}")

                    # Try to reconnect
                    if retry_count <= max_retries:
                        await self.disconnect()
                        if await self.connect_with_retry(1):  # Try once to reconnect
                            continue  # If reconnected successfully, retry the write

                if retry_count > max_retries:
                    logging.error(f"❌ Write failed after {max_retries} attempts: {e}")
                    self.is_connected = False
                    return False

                # Wait before retrying
                await asyncio.sleep(1)

    async def disconnect(self):
        """Disconnect from device"""
        if self.client and self.client.is_connected:
            try:
                logging.info(f"🔌 Disconnecting device: {self.device_alias}")
                await self.client.disconnect()
            except Exception as e:
                logging.error(f"⚠️ Error disconnecting: {e}")

        self.is_connected = False
        self.client = None
        return True
