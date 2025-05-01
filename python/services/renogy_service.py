"""
Service for handling Renogy device connections and data retrieval
"""
import logging
import asyncio
from renogybt import RoverClient, BatteryClient, LipoModel
from renogybt.DeviceManager import DeviceManager
from config.settings import DCDC_CONFIG, BATTERY_CONFIG
from controllers.socketio_controller import emit_event
import datetime

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class RenogyService:
    """Manages Renogy devices and provides data to the application"""

    def __init__(self):
        """Initialize the service"""
        # Create device manager
        self.device_manager = DeviceManager()

        # Create model
        self.lipo_model = LipoModel()

        # Data storage
        self.data = {
            'rng_ctrl': None,
            'rng_batt': None,
            'combined': None
        }

        self.running = False
        self.update_task = None
        self.initialized = False

    async def initialize(self):
        """Initialize all devices"""
        if self.initialized:
            return True

        # Create clients
        try:
            dcdc_client = RoverClient(DCDC_CONFIG)
            battery_client = BatteryClient(BATTERY_CONFIG)

            # Add clients to manager
            await self.device_manager.add_device('dcdc', dcdc_client)
            await self.device_manager.add_device('battery', battery_client)

            # Add data handler
            self.device_manager.add_data_handler(self.on_device_data)

            # Add error handler
            self.device_manager.add_error_handler(self.on_device_error)

            log.info("🚀 RenogyService initialized")
            self.initialized = True
            return True
        except Exception as e:
            log.error(f"❌ Error initializing RenogyService: {e}")
            return False

    def start(self):
        """Start the Renogy service (non-blocking)"""
        if self.running:
            log.warning("⚠️ Renogy service already running")
            return

        # Start in background
        self.running = True
        asyncio.create_task(self._start_async())
        log.info("▶️ Renogy service starting in background")

    async def _start_async(self):
        """Start the service asynchronously"""
        try:
            # Initialize devices if not already done
            if not self.initialized and not await self.initialize():
                log.error("❌ Failed to initialize Renogy service")
                self.running = False
                return

            # First, connect to all devices with retries
            log.info("🔌 Connecting to all devices...")
            max_attempts = 3
            attempt = 0

            while attempt < max_attempts:
                if await self.device_manager.connect_all_devices():
                    log.info("✅ Successfully connected to all devices")
                    break

                attempt += 1
                if attempt < max_attempts:
                    log.warning(f"🔄 Not all devices connected, retrying... (attempt {attempt}/{max_attempts})")
                    await asyncio.sleep(5)  # Wait before retrying
                else:
                    log.warning(f"⚠️ Failed to connect all devices after {max_attempts} attempts, continuing anyway")

            # Now start polling only connected devices
            log.info("📊 Starting polling...")
            await self.device_manager.start_polling()

            # Create update loop task for data processing
            self.update_task = asyncio.create_task(self._update_loop())

            log.info("✅ Renogy service started")
        except Exception as e:
            log.error(f"❌ Error starting Renogy service: {e}")
            self.running = False

    async def _update_loop(self):
        """Periodically update the model and emit data"""
        while self.running:
            try:
                # Check if devices are still connected before trying to update
                dcdc_connected = self.device_manager.is_device_connected('dcdc')
                battery_connected = self.device_manager.is_device_connected('battery')

                # Only update if both devices are connected and we have data
                if dcdc_connected and battery_connected and self.data['rng_ctrl'] and self.data['rng_batt']:
                    # Update model with latest data
                    self.lipo_model.update_data(self.data)
                    combined_data = self.lipo_model.calculate()

                    if combined_data and not combined_data.get('error'):
                        # Store for later retrieval
                        self.data['combined'] = combined_data

                        # Emit to websocket clients
                        await emit_event('renogy', 'data_update', combined_data)
                        log.debug("📡 Emitted combined Renogy data")
                elif not dcdc_connected or not battery_connected:
                    # Log which devices are disconnected
                    log.debug(f"📵 Skipping update - disconnected devices: " +
                              (f"DCDC, " if not dcdc_connected else "") +
                              (f"Battery" if not battery_connected else ""))
            except Exception as e:
                log.error(f"❌ Error in update loop: {e}")

            # Wait before checking again
            await asyncio.sleep(5)

    async def stop(self):
        """Stop the Renogy service"""
        if not self.running:
            return

        self.running = False

        # Cancel update task
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

        # Stop device manager
        await self.device_manager.stop()

        log.info("⏹️ Renogy service stopped")

    async def on_device_data(self, device_key, device, data):
        """Handle data from devices"""
        if device_key == 'dcdc':
            self.data['rng_ctrl'] = data
            log.debug(f"📥 Received data from DCDC device")
        elif device_key == 'battery':
            self.data['rng_batt'] = data
            log.debug(f"📥 Received data from Battery device")

    async def on_device_error(self, device_key, device, error):
        """Handle device errors"""
        log.error(f"⚠️ Device error ({device_key}): {error}")

        # Emit error event to websocket clients
        await emit_event('renogy', 'error', {
            'device': device_key,
            'message': error,
            'timestamp': str(datetime.datetime.now()),
            'code': 'CONNECTION_LOST' if 'connection loss' in error else 'DEVICE_ERROR'
        })

    def get_latest_data(self):
        """Get latest combined data"""
        return self.data.get('combined')

    def get_device_status(self):
        """Get status of all devices"""
        return {
            'dcdc_connected': self.device_manager.is_device_connected('dcdc'),
            'battery_connected': self.device_manager.is_device_connected('battery')
        }