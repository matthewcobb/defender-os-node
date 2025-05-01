import asyncio
import logging
from typing import Dict, Any, Callable, List, Optional

class DeviceManager:
    """
    Manages multiple Renogy BT devices and handles their connections and polling.
    Provides a unified interface for working with multiple devices.
    """

    def __init__(self):
        self.devices = {}  # Dictionary of device instances
        self.data_handlers = []  # List of data handler callbacks
        self.error_handlers = []  # List of error handler callbacks
        self.is_started = False
        self.started_event = asyncio.Event()

    async def add_device(self, device_key: str, device_instance):
        """Add a device to be managed"""
        self.devices[device_key] = device_instance

        # Setup callbacks
        device_instance.on_data_callback = self._on_device_data
        device_instance.on_error_callback = self._on_device_error

        # Start the device if manager is already running
        if self.is_started:
            await device_instance.start()

        return True

    async def start(self):
        """Start all devices"""
        if self.is_started:
            logging.warning("Device manager already started")
            return True

        self.is_started = True

        # Start all devices
        start_tasks = []
        for device_key, device in self.devices.items():
            start_tasks.append(asyncio.create_task(device.start()))

        # Wait for all devices to start
        if start_tasks:
            results = await asyncio.gather(*start_tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            logging.info(f"Started {success_count} of {len(start_tasks)} devices")

        self.started_event.set()
        return True

    async def stop(self):
        """Stop all devices"""
        if not self.is_started:
            return True

        # Stop all devices
        stop_tasks = []
        for device_key, device in self.devices.items():
            stop_tasks.append(asyncio.create_task(device.stop()))

        # Wait for all devices to stop
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

        self.is_started = False
        self.started_event.clear()
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