"""
Service for handling Renogy device connections and data retrieval
"""
import logging
import asyncio
from datetime import datetime
from renogybt import RoverClient, BatteryClient, LipoModel
from renogybt.DeviceManager import DeviceManager
from config.settings import DCDC_CONFIG, BATTERY_CONFIG, POLL_INTERVAL
from controllers.socketio_controller import emit_event

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
            'combined': None,
            'last_update': None
        }

        self.running = False
        self.update_task = None

    async def initialize(self):
        """Initialize all devices and start services"""
        # Create DCDC client
        dcdc_client = RoverClient(DCDC_CONFIG)

        # Create Battery client
        battery_client = BatteryClient(BATTERY_CONFIG)

        # Add clients to manager
        await self.device_manager.add_device('dcdc', dcdc_client)
        await self.device_manager.add_device('battery', battery_client)

        # Add data handler
        self.device_manager.add_data_handler(self.on_device_data)

        # Add error handler
        self.device_manager.add_error_handler(self.on_device_error)

        log.info("RenogyService initialized")
        return True

    def start(self):
        """Start the Renogy service (non-blocking)"""
        if self.running:
            log.warning("Renogy service already running")
            return

        # Start in background
        self.running = True
        asyncio.create_task(self._start_async())
        log.info("Renogy service starting in background")

    async def _start_async(self):
        """Start the service asynchronously"""
        try:
            # Initialize devices
            await self.initialize()

            # Start the device manager
            await self.device_manager.start()

            # Create update loop task
            self.update_task = asyncio.create_task(self._update_loop())

            log.info("Renogy devices started successfully")
        except Exception as e:
            log.error(f"Error starting Renogy service: {e}")
            self.running = False

    async def _update_loop(self):
        """Periodically update the model and emit data"""
        while self.running:
            try:
                # Only update if we have both device data
                if self.data['rng_ctrl'] and self.data['rng_batt']:
                    # Update model with latest data
                    self.lipo_model.update_data(self.data)
                    combined_data = self.lipo_model.calculate()

                    if combined_data and not combined_data.get('error'):
                        # Store for later retrieval
                        self.data['combined'] = combined_data
                        self.data['last_update'] = datetime.now().isoformat()

                        # Emit to websocket clients
                        await emit_event('renogy', 'data_update', combined_data)
                        log.debug("Emitted combined Renogy data update")
            except Exception as e:
                log.error(f"Error in update loop: {e}")

            # Wait before checking again
            await asyncio.sleep(2)

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

        log.info("Renogy service stopped")

    async def on_device_data(self, device_key, device, data):
        """Handle data from devices"""
        if device_key == 'dcdc':
            self.data['rng_ctrl'] = data
            log.debug(f"Received data from DCDC device")
        elif device_key == 'battery':
            self.data['rng_batt'] = data
            log.debug(f"Received data from Battery device")

    async def on_device_error(self, device_key, device, error):
        """Handle device errors"""
        log.error(f"Device error ({device_key}): {error}")

        # Emit error to frontend
        error_data = {
            'device_type': device_key,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        }
        await emit_event('renogy', 'error', error_data)

    def get_latest_data(self):
        """Get latest combined data"""
        return self.data.get('combined')

    def get_device_status(self):
        """Get status of all devices"""
        return {
            'dcdc_connected': bool(self.data.get('rng_ctrl')),
            'battery_connected': bool(self.data.get('rng_batt')),
            'last_update': self.data.get('last_update')
        }