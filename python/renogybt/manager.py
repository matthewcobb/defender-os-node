"""
Device manager for multiple Renogy BT devices
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional

from .device import Device

class DeviceManager:
    """
    Simplified manager for multiple Renogy BT devices with sequential polling
    """

    def __init__(self):
        """Initialize an empty device manager"""
        self.devices = {}
        self.data_handlers = []
        self.error_handlers = []
        self.connecting = False

    async def add_device(self, device_key: str, device: Device) -> bool:
        """
        Add a device to the manager

        Args:
            device_key: Unique key to identify the device
            device: Device instance

        Returns:
            bool: True if added successfully
        """
        # Check if this device key already exists
        if device_key in self.devices:
            logging.warning(f"⚠️ Device key already exists: {device_key}")
            return False

        # Set callbacks to route through manager
        device.on_data_callback = self._on_device_data
        device.on_error_callback = self._on_device_error

        # Add device to collection
        self.devices[device_key] = device
        logging.info(f"➕ Added device to manager: {device_key}")
        return True

    async def connect_all_devices(self, max_attempts: int = 3) -> bool:
        """
        Connect all managed devices

        Args:
            max_attempts: Maximum connection attempts per device

        Returns:
            bool: True if all devices connected successfully
        """
        if not self.devices:
            logging.warning("🔍 No devices to connect")
            return False

        if self.connecting:
            logging.info("⏳ Already connecting devices")
            return False

        self.connecting = True

        try:
            logging.info(f"🔌 Connecting {len(self.devices)} devices...")

            # Connect each device sequentially
            all_connected = True
            for device_key, device in self.devices.items():
                logging.info(f"🔄 Connecting device: {device_key}")

                if not await device.connect(max_attempts):
                    logging.warning(f"❗ Failed to connect to {device_key}")
                    all_connected = False
                else:
                    logging.info(f"✅ Device {device_key} connected successfully")

            if all_connected:
                logging.info(f"✅ All devices connected successfully")
            else:
                logging.warning(f"⚠️ Not all devices connected")

            return all_connected

        finally:
            self.connecting = False

    async def start_polling(self, sequential_delay: float = 2.0) -> bool:
        """
        Start polling all connected devices

        Args:
            sequential_delay: Delay between starting polling for each device

        Returns:
            bool: True if polling started for at least one device
        """
        connected_devices = []

        # Identify connected devices
        for device_key, device in self.devices.items():
            if device.connection.is_connected:
                connected_devices.append((device_key, device))
                logging.info(f"🟢 Device ready for polling: {device_key}")
            else:
                logging.warning(f"🔴 Cannot poll device: {device_key} not connected")

        if not connected_devices:
            logging.warning("⚠️ No connected devices to poll")
            return False

        # Start polling each device sequentially
        logging.info(f"🔄 Starting sequential polling for {len(connected_devices)} devices")

        for idx, (device_key, device) in enumerate(connected_devices):
            logging.info(f"📊 Starting polling for device: {device_key}")
            await device.start_polling()

            # Add delay between starting polling for each device
            # This prevents overwhelming the BLE stack
            if idx < len(connected_devices) - 1:
                await asyncio.sleep(sequential_delay)

        logging.info(f"✅ Started polling for all {len(connected_devices)} devices")
        return True

    async def stop(self) -> bool:
        """
        Stop all devices (polling and disconnect)

        Returns:
            bool: True when all devices stopped
        """
        if not self.devices:
            return True

        stop_tasks = []

        for device in self.devices.values():
            stop_tasks.append(asyncio.create_task(device.disconnect()))

        # Wait for all devices to stop
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
            logging.info("⏹️ All devices stopped")

        return True

    def add_data_handler(self, handler: Callable) -> None:
        """
        Add a callback for device data updates

        Args:
            handler: Callback function(device_key, device, data)
        """
        if handler not in self.data_handlers:
            self.data_handlers.append(handler)

    def remove_data_handler(self, handler: Callable) -> None:
        """
        Remove a data handler callback

        Args:
            handler: Handler to remove
        """
        if handler in self.data_handlers:
            self.data_handlers.remove(handler)

    def add_error_handler(self, handler: Callable) -> None:
        """
        Add a callback for device errors

        Args:
            handler: Callback function(device_key, device, error)
        """
        if handler not in self.error_handlers:
            self.error_handlers.append(handler)

    def remove_error_handler(self, handler: Callable) -> None:
        """
        Remove an error handler callback

        Args:
            handler: Handler to remove
        """
        if handler in self.error_handlers:
            self.error_handlers.remove(handler)

    async def _on_device_data(self, device: Device, data: Dict[str, Any]) -> None:
        """
        Internal callback for device data

        Args:
            device: Source device
            data: Device data
        """
        device_key = next((k for k, v in self.devices.items() if v == device), None)

        if device_key:
            # Call all registered data handlers
            for handler in self.data_handlers:
                try:
                    await handler(device_key, device, data)
                except Exception as e:
                    logging.error(f"❌ Error in data handler: {e}")

    async def _on_device_error(self, device: Device, error: str) -> None:
        """
        Internal callback for device errors

        Args:
            device: Source device
            error: Error message
        """
        device_key = next((k for k, v in self.devices.items() if v == device), None)

        if device_key:
            # Call all registered error handlers
            for handler in self.error_handlers:
                try:
                    await handler(device_key, device, error)
                except Exception as e:
                    logging.error(f"❌ Error in error handler: {e}")

    def get_device(self, device_key: str) -> Optional[Device]:
        """
        Get a device by key

        Args:
            device_key: Device key

        Returns:
            Device instance or None if not found
        """
        return self.devices.get(device_key)

    def get_device_count(self) -> int:
        """
        Get the number of managed devices

        Returns:
            int: Number of devices
        """
        return len(self.devices)

    def is_device_connected(self, device_key: str) -> bool:
        """
        Check if a specific device is connected

        Args:
            device_key: Device key

        Returns:
            bool: True if device is connected
        """
        device = self.devices.get(device_key)
        return device is not None and device.connection.is_connected