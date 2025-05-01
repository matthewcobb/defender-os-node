import asyncio
import logging

class DeviceManager:
    """
    Simple manager for multiple Renogy BT devices
    """

    def __init__(self):
        self.devices = {}  # Dictionary of device instances
        self.data_handlers = []  # Callbacks for data
        self.error_handlers = []  # Callbacks for errors
        self.connecting = False

    async def add_device(self, device_key, device_instance):
        """Add a device to be managed"""
        self.devices[device_key] = device_instance

        # Setup callbacks
        device_instance.on_data_callback = self._on_device_data
        device_instance.on_error_callback = self._on_device_error
        return True

    async def connect_all_devices(self, max_attempts=3):
        """Connect all devices, waiting for all to connect before returning

        Args:
            max_attempts: Maximum number of connection attempts per device

        Returns:
            bool: True if all devices connected successfully
        """
        if not self.devices:
            logging.warning("No devices to connect")
            return False

        if self.connecting:
            logging.info("Already connecting devices")
            return False

        self.connecting = True

        try:
            logging.info(f"Connecting {len(self.devices)} devices...")

            # Try to connect each device sequentially with retry
            all_connected = True
            for device_key, device in self.devices.items():
                if not device.ble_manager:
                    logging.error(f"Device {device_key} has no BLE manager")
                    all_connected = False
                    continue

                logging.info(f"Connecting device: {device_key}")
                if not await device.ble_manager.connect_with_retry(max_attempts):
                    logging.warning(f"Failed to connect to {device_key}")
                    all_connected = False
                else:
                    logging.info(f"Device {device_key} connected successfully")

            if all_connected:
                logging.info(f"All devices connected successfully")
            else:
                logging.warning(f"Not all devices connected")

            return all_connected
        finally:
            self.connecting = False

    async def start_polling(self):
        """Start polling for all devices"""
        poll_tasks = []

        # Only start polling for connected devices
        for device_key, device in self.devices.items():
            if device.ble_manager and device.ble_manager.is_connected:
                poll_tasks.append(device.start_polling())
                logging.info(f"Starting polling for device: {device_key}")
            else:
                logging.warning(f"Cannot start polling for {device_key}: not connected")

        if poll_tasks:
            await asyncio.gather(*poll_tasks)
            logging.info(f"Started polling for {len(poll_tasks)} devices")
        else:
            logging.warning("No connected devices to poll")

    async def stop(self):
        """Stop all devices"""
        stop_tasks = []
        for device in self.devices.values():
            stop_tasks.append(asyncio.create_task(device.stop()))

        # Wait for all devices to stop
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
            logging.info("All devices stopped")
        return True

    def add_data_handler(self, handler):
        """Add a callback for device data updates"""
        if handler not in self.data_handlers:
            self.data_handlers.append(handler)

    def remove_data_handler(self, handler):
        """Remove a data handler callback"""
        if handler in self.data_handlers:
            self.data_handlers.remove(handler)

    def add_error_handler(self, handler):
        """Add a callback for device errors"""
        if handler not in self.error_handlers:
            self.error_handlers.append(handler)

    def remove_error_handler(self, handler):
        """Remove an error handler callback"""
        if handler in self.error_handlers:
            self.error_handlers.remove(handler)

    async def _on_device_data(self, device, data):
        """Internal callback for device data"""
        device_key = next((k for k, v in self.devices.items() if v == device), None)
        if device_key:
            # Call all registered data handlers
            for handler in self.data_handlers:
                try:
                    await handler(device_key, device, data)
                except Exception as e:
                    logging.error(f"Error in data handler: {e}")

    async def _on_device_error(self, device, error):
        """Internal callback for device errors"""
        device_key = next((k for k, v in self.devices.items() if v == device), None)
        if device_key:
            # Call all registered error handlers
            for handler in self.error_handlers:
                try:
                    await handler(device_key, device, error)
                except Exception as e:
                    logging.error(f"Error in error handler: {e}")

    def get_device(self, device_key):
        """Get a device by key"""
        return self.devices.get(device_key)

    def get_device_count(self):
        """Get number of managed devices"""
        return len(self.devices)

    def is_device_connected(self, device_key):
        """Check if a specific device is connected"""
        device = self.devices.get(device_key)
        if device and device.ble_manager:
            return device.ble_manager.is_connected
        return False