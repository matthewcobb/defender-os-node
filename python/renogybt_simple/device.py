"""
Simplified Renogy device base class
"""

import asyncio
import logging
from typing import List, Dict, Any, Callable, Optional, Union, Tuple

from .connection import BleConnection
from .utils import crc16_modbus, ModbusFunction
from config.settings import POLL_INTERVAL

class Device:
    """
    Base class for Renogy BT devices that handles the Modbus protocol
    """

    def __init__(self,
                 mac_address: str,
                 name: str = None,
                 device_id: int = 1,
                 on_data_callback: Callable = None,
                 on_error_callback: Callable = None):
        """
        Initialize the device with required configuration

        Args:
            mac_address: MAC address of the device
            name: Name/alias of the device (default: based on MAC)
            device_id: Modbus device ID (default: 1)
            on_data_callback: Callback for device data updates
            on_error_callback: Callback for device errors
        """
        self.mac_address = mac_address
        self.name = name if name else f"Renogy-{mac_address[-5:].replace(':', '')}"
        self.device_id = device_id
        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback

        # Internal state
        self.data = {}
        self.polling = False
        self.polling_task = None
        self._sections = []  # List of register sections to read
        self._current_section = 0
        self._poll_lock = asyncio.Lock()
        self._pending_futures = {}  # For write operations

        # Create BLE connection
        self.connection = BleConnection(
            mac_address=mac_address,
            name=self.name,
            data_callback=self._on_data_received
        )

        logging.info(f"✨ Initialized device: {self.name}")

    async def connect(self, max_attempts: int = 3) -> bool:
        """
        Connect to the device

        Args:
            max_attempts: Maximum connection attempts

        Returns:
            bool: True if connected successfully
        """
        return await self.connection.connect(max_attempts)

    async def disconnect(self) -> bool:
        """
        Disconnect from the device

        Returns:
            bool: True if disconnected successfully
        """
        # Stop polling first
        if self.polling:
            await self.stop_polling()

        return await self.connection.disconnect()

    async def start_polling(self) -> bool:
        """
        Start polling the device for data

        Returns:
            bool: True if polling started successfully
        """
        if self.polling:
            logging.warning(f"🔄 Already polling device: {self.name}")
            return True

        if not self._sections:
            logging.error(f"❌ No sections defined for device: {self.name}")
            return False

        if not await self.connection.ensure_connected():
            logging.error(f"❌ Cannot start polling: {self.name} not connected")
            return False

        self.polling = True
        self.polling_task = asyncio.create_task(self._polling_loop())
        logging.info(f"🔄 Started polling device: {self.name}")
        return True

    async def stop_polling(self) -> bool:
        """
        Stop polling the device

        Returns:
            bool: True if polling stopped successfully
        """
        self.polling = False

        if self.polling_task and not self.polling_task.done():
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass

        logging.info(f"⏹️ Stopped polling: {self.name}")
        return True

    async def read_register(self, register: int, word_count: int = 1) -> bool:
        """
        Read a register from the device

        Args:
            register: Register address
            word_count: Number of words to read

        Returns:
            bool: True if read command was sent successfully
        """
        # Create modbus read command
        cmd = self._create_read_command(register, word_count)
        return await self.connection.write(cmd)

    async def write_register(self, register: int, value: int) -> bool:
        """
        Write a value to a register

        Args:
            register: Register address
            value: Value to write

        Returns:
            bool: True if write was successful
        """
        # Create a future to wait for the response
        future = asyncio.get_event_loop().create_future()
        cmd_id = (register, value)
        self._pending_futures[cmd_id] = future

        # Create modbus write command
        cmd = self._create_write_command(register, value)

        # Send command
        if not await self.connection.write(cmd):
            del self._pending_futures[cmd_id]
            return False

        # Wait for response with timeout
        try:
            return await asyncio.wait_for(future, 5)  # 5 second timeout
        except asyncio.TimeoutError:
            logging.error(f"⏱️ Timeout writing to register {register}")
            if cmd_id in self._pending_futures:
                del self._pending_futures[cmd_id]
            return False

    def add_section(self, register: int, word_count: int, parser: Callable = None) -> None:
        """
        Add a register section to poll

        Args:
            register: Register address
            word_count: Number of words to read
            parser: Optional function to parse the response
        """
        if register < 0 or word_count <= 0:
            logging.error(f"❌ Invalid section: register={register}, words={word_count}")
            return

        self._sections.append({
            'register': register,
            'words': word_count,
            'parser': parser
        })
        logging.info(f"➕ Added polling section: reg={register}, words={word_count}")

    async def _polling_loop(self) -> None:
        """Internal polling loop for the device"""
        try:
            while self.polling:
                async with self._poll_lock:
                    try:
                        # Verify connection
                        if not await self.connection.ensure_connected():
                            raise Exception(f"Device {self.name} not connected")

                        # Read current section
                        await self._read_next_section()

                        # Small delay between reads
                        await asyncio.sleep(0.8)

                    except Exception as e:
                        logging.error(f"⚠️ Error polling {self.name}: {e}")

                        if self.on_error_callback:
                            try:
                                await self.on_error_callback(self, str(e))
                            except Exception as callback_error:
                                logging.error(f"❌ Error in error callback: {callback_error}")

                        # If connection issues, try to reconnect
                        if not self.connection.is_connected:
                            logging.warning(f"📵 Connection lost to {self.name}, attempting to reconnect...")

                            # Disconnect first
                            await self.connection.disconnect()
                            await asyncio.sleep(2)  # Small delay before reconnect

                            # Try to reconnect
                            success = await self.connection.connect(3)
                            if not success:
                                logging.error(f"❌ Failed to reconnect to {self.name}")
                                self.polling = False
                                break

                            # Successfully reconnected
                            logging.info(f"✅ Successfully reconnected to {self.name}")
                            await asyncio.sleep(2)

                # Sleep between polling cycles
                await asyncio.sleep(POLL_INTERVAL)

        except asyncio.CancelledError:
            # Normal cancellation
            logging.info(f"⏹️ Polling task cancelled for {self.name}")
            raise

        except Exception as e:
            logging.error(f"❌ Unexpected error in polling loop: {e}")
            self.polling = False

            if self.on_error_callback:
                try:
                    await self.on_error_callback(self, f"Polling error: {str(e)}")
                except Exception:
                    pass

    async def _read_next_section(self) -> bool:
        """Read the next section from the device"""
        if not self._sections:
            return False

        section = self._sections[self._current_section]
        result = await self.read_register(section['register'], section['words'])

        # Move to next section for next poll
        self._current_section = (self._current_section + 1) % len(self._sections)

        return result

    async def _on_data_received(self, data: bytearray) -> None:
        """
        Handle data received from the device

        Args:
            data: Data received from the device
        """
        if len(data) < 3:
            logging.warning(f"⚠️ Received data too short: {data.hex()}")
            return

        function_code = data[1]

        # Handle error response
        if function_code == ModbusFunction.ERROR:
            error_msg = f"Device reported error: {data.hex()}"
            logging.error(f"⚠️ {error_msg}")

            if self.on_error_callback:
                await self.on_error_callback(self, error_msg)

            return

        # Handle read response
        if function_code == ModbusFunction.READ and len(data) > 5:
            section_idx = (self._current_section - 1) % len(self._sections)
            section = self._sections[section_idx]

            if section.get('parser'):
                try:
                    section['parser'](data)
                except Exception as e:
                    logging.error(f"⚠️ Error parsing data: {e}")

            # Notify data callback after processing full cycle
            if self._current_section == 0 and self.on_data_callback:
                try:
                    await self.on_data_callback(self, self.data.copy())
                except Exception as e:
                    logging.error(f"❌ Error in data callback: {e}")

        # Handle write response
        elif function_code == ModbusFunction.WRITE and len(data) >= 5:
            # Extract register and value from response
            register = (data[2] << 8) | data[3]
            value = (data[4] << 8) | data[5]

            # Complete any pending futures for this write
            completed = False
            cmd_id = (register, value)

            if cmd_id in self._pending_futures:
                self._pending_futures[cmd_id].set_result(True)
                del self._pending_futures[cmd_id]
                completed = True

            # Try with just the register if exact match not found
            if not completed:
                for pending_id in list(self._pending_futures.keys()):
                    if pending_id[0] == register:
                        self._pending_futures[pending_id].set_result(True)
                        del self._pending_futures[pending_id]
                        break

    def _create_read_command(self, register: int, word_count: int) -> bytearray:
        """
        Create a Modbus read command

        Args:
            register: Register address
            word_count: Number of words to read

        Returns:
            bytearray: Command bytes
        """
        cmd = [
            self.device_id,
            ModbusFunction.READ,
            register >> 8,
            register & 0xFF,
            word_count >> 8,
            word_count & 0xFF
        ]

        # Calculate CRC
        crc = crc16_modbus(bytes(cmd))
        cmd.append(crc[0])
        cmd.append(crc[1])

        return bytearray(cmd)

    def _create_write_command(self, register: int, value: int) -> bytearray:
        """
        Create a Modbus write command

        Args:
            register: Register address
            value: Value to write

        Returns:
            bytearray: Command bytes
        """
        cmd = [
            self.device_id,
            ModbusFunction.WRITE,
            register >> 8,
            register & 0xFF,
            value >> 8,
            value & 0xFF
        ]

        # Calculate CRC
        crc = crc16_modbus(bytes(cmd))
        cmd.append(crc[0])
        cmd.append(crc[1])

        return bytearray(cmd)