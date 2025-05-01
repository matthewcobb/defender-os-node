"""
Service for handling Renogy device connections and data retrieval
"""
import logging
import asyncio
import threading
from datetime import datetime
from renogybt import RoverClient, BatteryClient, LipoModel, Utils
from config.settings import DCDC_CONFIG, BATTERY_CONFIG
from controllers.socketio_controller import emit_event

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class RenogyService:
    """Async-compatible wrapper for Renogy services that runs clients in a separate thread"""

    def __init__(self):
        """Initialize the service"""
        self.dcdc_client = RoverClient(
            DCDC_CONFIG,
            on_data_callback=self.on_data_received,
            on_error_callback=self.on_error
        )

        self.battery_client = BatteryClient(
            BATTERY_CONFIG,
            on_data_callback=self.on_data_received,
            on_error_callback=self.on_error
        )

        self.data = {
            'rng_ctrl': None,
            'rng_batt': None,
            'combined': None
        }
        self.thread = None
        self.running = False

    def start(self):
        """Start the Renogy clients in a separate thread to avoid event loop conflicts"""
        if self.running:
            log.warning("Renogy service already running")
            return

        self.running = True

        # Create and start a thread for the clients to run in their own event loop
        self.thread = threading.Thread(target=self._run_clients)
        self.thread.daemon = True  # Allow the thread to be terminated when the app exits
        self.thread.start()

        log.info("Renogy service thread started")

    def _run_clients(self):
        """Run clients in a dedicated thread with their own event loop"""
        try:
            # Create an event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Start both clients
            self.dcdc_client.start()
            self.battery_client.start()

            log.info("Renogy clients started in separate thread")
        except Exception as e:
            log.error(f"Error in Renogy thread: {e}")
            self.running = False

    def stop(self):
        """Stop the Renogy clients"""
        if not self.running:
            return

        self.running = False

        # Run stop operations in the thread's event loop
        try:
            # These stop operations will run in the client's own event loop
            self.dcdc_client.stop()
            self.battery_client.stop()

            log.info("Renogy clients stopped")
        except Exception as e:
            log.error(f"Error stopping Renogy clients: {e}")

    def on_data_received(self, client, data):
        """Callback when data is received from either client"""
        client_type = client.client_config.get('type', 'unknown')
        log.debug(f"Received data from {client_type}")
        self.data[client_type] = data
        self.update_model_and_emit()

    def update_model_and_emit(self):
        """Update the LipoModel and emit combined data"""
        if not self.data['rng_ctrl'] or not self.data['rng_batt']:
            return  # Don't process until we have both

        # Update the model with latest data
        combined_data = LipoModel(self.data).calculate()

        if combined_data:
            # Store for later retrieval
            self.data['combined'] = combined_data

            # Emit to websocket clients
            asyncio.create_task(emit_event('renogy', 'data_update', combined_data))
            log.debug("Emitted combined Renogy data update")

    def on_error(self, client, error):
        """Handle errors from clients"""
        device_type = client.client_config.get('type', 'unknown').lower()
        log.error(f"Renogy client error ({device_type}): {error}")

        # Emit error to frontend
        error_data = {
            'device_type': device_type,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        }
        asyncio.create_task(emit_event('renogy', 'error', error_data))