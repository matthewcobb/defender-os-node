"""
Simplified BLE connection handling for Renogy devices
"""

import asyncio
import logging
from bleak import BleakClient, BleakScanner

# Default configuration
DEFAULT_DISCOVERY_TIMEOUT = 10  # seconds
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 5  # seconds
DEFAULT_MAX_RETRY_DELAY = 30  # seconds

# Default service UUIDs
DEFAULT_WRITE_SERVICE_UUID = "0000ffd0-0000-1000-8000-00805f9b34fb"
DEFAULT_NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
DEFAULT_WRITE_CHAR_UUID = "0000ffd1-0000-1000-8000-00805f9b34fb"

class BleConnection:
    """
    Manages BLE connection to a Renogy device with automatic reconnection
    """

    def __init__(self, mac_address, name, data_callback=None,
                 write_service_uuid=DEFAULT_WRITE_SERVICE_UUID,
                 notify_char_uuid=DEFAULT_NOTIFY_CHAR_UUID,
                 write_char_uuid=DEFAULT_WRITE_CHAR_UUID):
        """
        Initialize a BLE connection

        Args:
            mac_address: MAC address of the device
            name: Name/alias of the device for logging
            data_callback: Function to call when data is received
            write_service_uuid: UUID of the write service
            notify_char_uuid: UUID of the notify characteristic
            write_char_uuid: UUID of the write characteristic
        """
        self.mac_address = mac_address.upper()
        self.name = name
        self.data_callback = data_callback
        self.write_service_uuid = write_service_uuid
        self.notify_char_uuid = notify_char_uuid
        self.write_char_uuid = write_char_uuid

        # Connection state
        self.device = None
        self.client = None
        self.write_char_handle = None
        self.is_connected = False
        self._connection_lock = asyncio.Lock()

    async def discover(self, timeout=DEFAULT_DISCOVERY_TIMEOUT):
        """
        Discover the device

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            bool: True if device was found
        """
        logging.info(f"🔍 Discovering device: {self.name}")

        try:
            discovered_devices = await BleakScanner.discover(timeout=timeout)

            for device in discovered_devices:
                # Match by MAC address (preferred) or name
                if (device.address and device.address.upper() == self.mac_address or
                   (device.name and device.name.strip() == self.name)):
                    logging.info(f"✅ Found device: {device.name} ({device.address})")
                    self.device = device
                    return True

            logging.warning(f"❌ Device not found: {self.name}")
            return False
        except Exception as e:
            logging.error(f"❌ Error during discovery: {e}")
            return False

    async def connect(self, max_attempts=DEFAULT_RETRY_ATTEMPTS):
        """
        Connect to the device with automatic retries

        Args:
            max_attempts: Maximum number of connection attempts (0 = infinite)

        Returns:
            bool: True if successfully connected
        """
        async with self._connection_lock:
            # Already connected
            if self.is_connected and self.client and self.client.is_connected:
                return True

            attempts = 0
            retry_delay = DEFAULT_RETRY_DELAY

            while max_attempts == 0 or attempts < max_attempts:
                # Discover device if needed
                if not self.device and not await self.discover():
                    attempts += 1
                    await self._handle_connection_failure(
                        f"Discovery failed (attempt {attempts}/{max_attempts})",
                        retry_delay
                    )
                    retry_delay = min(retry_delay * 1.5, DEFAULT_MAX_RETRY_DELAY)
                    continue

                # Try to connect
                try:
                    logging.info(f"🔌 Connecting to {self.name}...")

                    # Clean up previous client if any
                    if self.client:
                        await self._disconnect_client()

                    # Create new client and connect
                    self.client = BleakClient(self.device)
                    await self.client.connect()

                    if not self.client.is_connected:
                        attempts += 1
                        await self._handle_connection_failure(
                            f"Connection failed (attempt {attempts}/{max_attempts})",
                            retry_delay
                        )
                        retry_delay = min(retry_delay * 1.5, DEFAULT_MAX_RETRY_DELAY)
                        continue

                    # Wait for service discovery to complete
                    await asyncio.sleep(1)

                    # Setup notifications and find write characteristic
                    self.is_connected = True
                    service_found = False

                    for service in self.client.services:
                        for char in service.characteristics:
                            # Set up notification handler
                            if char.uuid == self.notify_char_uuid:
                                await self.client.start_notify(char, self._notification_handler)
                                logging.info(f"📡 Subscribed to notifications: {char.uuid}")

                            # Find write characteristic
                            if char.uuid == self.write_char_uuid and service.uuid == self.write_service_uuid:
                                self.write_char_handle = char.handle
                                service_found = True
                                logging.info(f"📝 Found write characteristic: {char.uuid}")

                    if not service_found:
                        self.is_connected = False
                        attempts += 1
                        await self._handle_connection_failure(
                            "Service discovery failed - required characteristic not found",
                            retry_delay
                        )
                        retry_delay = min(retry_delay * 1.5, DEFAULT_MAX_RETRY_DELAY)
                        continue

                    logging.info(f"✅ Connected to {self.name}")
                    return True

                except Exception as e:
                    attempts += 1
                    await self._handle_connection_failure(
                        f"Connection error: {e} (attempt {attempts}/{max_attempts})",
                        retry_delay
                    )
                    retry_delay = min(retry_delay * 1.5, DEFAULT_MAX_RETRY_DELAY)

            logging.error(f"❌ Failed to connect to {self.name} after {attempts} attempts")
            return False

    async def ensure_connected(self, max_attempts=2):
        """
        Ensure the device is connected, reconnecting if necessary

        Args:
            max_attempts: Maximum number of connection attempts

        Returns:
            bool: True if connected successfully
        """
        if not self.is_connected or not self.client or not self.client.is_connected:
            logging.warning(f"📵 Device {self.name} not connected, attempting to reconnect")
            return await self.connect(max_attempts)

        # Check if service discovery is complete
        if self.write_char_handle is None:
            logging.warning(f"⚠️ Service discovery not complete for {self.name}, reconnecting")
            await self.disconnect()
            return await self.connect(max_attempts)

        return True

    async def write(self, data, max_retries=2):
        """
        Write data to the device

        Args:
            data: Data to write (list or bytes)
            max_retries: Maximum retries for write operations

        Returns:
            bool: True if write was successful
        """
        if not await self.ensure_connected():
            return False

        retry_count = 0

        while retry_count <= max_retries:
            try:
                await self.client.write_gatt_char(
                    self.write_char_handle,
                    bytearray(data) if not isinstance(data, bytearray) else data,
                    response=False
                )
                return True

            except Exception as e:
                retry_count += 1
                error_msg = str(e)

                # Service discovery error requires reconnection
                if "Service Discovery" in error_msg:
                    logging.warning(f"⚙️ Service discovery error on write, attempt {retry_count}/{max_retries}")

                    if retry_count <= max_retries:
                        await self.disconnect()
                        if await self.connect(1):  # Try once to reconnect
                            continue

                if retry_count > max_retries:
                    logging.error(f"❌ Write failed after {max_retries} attempts: {e}")
                    self.is_connected = False
                    return False

                # Wait before retrying
                await asyncio.sleep(1)

    async def disconnect(self):
        """
        Disconnect from the device

        Returns:
            bool: True if disconnected successfully
        """
        if self.client and self.client.is_connected:
            try:
                logging.info(f"🔌 Disconnecting from {self.name}")
                await self.client.disconnect()
            except Exception as e:
                logging.error(f"⚠️ Error disconnecting: {e}")

        self.is_connected = False
        self.client = None
        self.write_char_handle = None
        return True

    async def _notification_handler(self, _sender, data):
        """
        Handle incoming notifications from the device

        Args:
            _sender: The sender object (unused)
            data: The received data
        """
        if self.data_callback:
            await self.data_callback(data)

    async def _disconnect_client(self):
        """Safely disconnect the client"""
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass  # Ignore errors during cleanup

    async def _handle_connection_failure(self, message, retry_delay):
        """
        Handle connection failure with logging and delay

        Args:
            message: Error message to log
            retry_delay: Delay before next retry
        """
        logging.warning(f"⚠️ {message}, retrying in {retry_delay}s")
        await asyncio.sleep(retry_delay)