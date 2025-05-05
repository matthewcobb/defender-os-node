"""
Service for handling Renogy device connections and data retrieval using the simplified renogybt_simple library
"""
import logging
import asyncio
import datetime
from typing import Dict, Any, Optional

# Import from the simplified library
from renogybt_simple import DeviceManager, RoverDevice, BatteryDevice, LipoModel
from config.settings import DCDC_CONFIG, BATTERY_CONFIG, POLL_INTERVAL, TEMPERATURE_UNIT
from controllers.socketio_controller import emit_event

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class RenogySimpleService:
    """Manages Renogy devices using simplified library and provides data to the application"""

    def __init__(self):
        """Initialize the service"""
        # Create device manager
        self.device_manager = DeviceManager()

        # Create battery model calculator
        self.lipo_model = LipoModel()

        # Data storage
        self.data = {
            'dcdc': None,
            'battery': None,
            'combined': None
        }

        self.running = False
        self.update_task = None
        self.initialized = False

    async def initialize(self):
        """Initialize all devices"""
        if self.initialized:
            return True

        try:
            # Create devices
            log.info("📱 Creating Renogy devices...")

            # Create the DCDC device
            dcdc_device = RoverDevice(
                mac_address=DCDC_CONFIG['mac_addr'],
                name=DCDC_CONFIG['alias'],
                device_id=DCDC_CONFIG['device_id']
            )

            # Create the Battery device
            battery_device = BatteryDevice(
                mac_address=BATTERY_CONFIG['mac_addr'],
                name=BATTERY_CONFIG['alias'],
                device_id=BATTERY_CONFIG['device_id']
            )

            # Add devices to manager
            await self.device_manager.add_device('dcdc', dcdc_device)
            await self.device_manager.add_device('battery', battery_device)

            # Register event handlers
            self.device_manager.add_data_handler(self.on_device_data)
            self.device_manager.add_error_handler(self.on_device_error)

            log.info("🚀 RenogySimpleService initialized")
            self.initialized = True
            return True
        except Exception as e:
            log.error(f"❌ Error initializing RenogySimpleService: {e}")
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

            # Connect to all devices with retries
            log.info("🔌 Connecting to all devices...")
            max_attempts = 3

            if await self.device_manager.connect_all_devices(max_attempts):
                log.info("✅ Successfully connected to all devices")
            else:
                log.warning(f"⚠️ Not all devices connected after {max_attempts} attempts, continuing anyway")

            # Start polling for connected devices
            log.info("📊 Starting sequential polling...")
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
                # Check if devices are still connected
                dcdc_connected = self.device_manager.is_device_connected('dcdc')
                battery_connected = self.device_manager.is_device_connected('battery')

                # Only update if both devices are connected and we have data
                if dcdc_connected and battery_connected and self.data['dcdc'] and self.data['battery']:
                    # Use the LipoModel to combine data and calculate time estimates
                    combined_data = self.lipo_model.calculate(self.data['dcdc'], self.data['battery'])

                    if combined_data and 'error' not in combined_data:
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
            await asyncio.sleep(1.5)

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

    async def on_device_data(self, device_key: str, device: Any, data: Dict[str, Any]) -> None:
        """Handle data from devices"""
        log.info(f"📥 Received data from {device_key} device: {data}")
        if device_key == 'dcdc':
            self.data['dcdc'] = data
            log.debug(f"📥 Received data from DCDC device")
        elif device_key == 'battery':
            self.data['battery'] = data
            log.debug(f"📥 Received data from Battery device")

    async def on_device_error(self, device_key: str, device: Any, error: str) -> None:
        """Handle device errors"""
        log.error(f"⚠️ Device error ({device_key}): {error}")

        # Emit error event to websocket clients
        await emit_event('renogy', 'error', {
            'device': device_key,
            'message': error,
            'timestamp': str(datetime.datetime.now()),
            'code': 'CONNECTION_LOST' if 'connection loss' in str(error) else 'DEVICE_ERROR'
        })

    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """Get latest combined data"""
        return self.data.get('combined')

    def get_device_status(self) -> Dict[str, bool]:
        """Get status of all devices"""
        return {
            'dcdc_connected': self.device_manager.is_device_connected('dcdc'),
            'battery_connected': self.device_manager.is_device_connected('battery')
        }