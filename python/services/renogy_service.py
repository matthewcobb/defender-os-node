"""
Service for handling Renogy device connections and data retrieval
"""
import logging
import asyncio
from datetime import datetime
from renogybt import RoverClient, BatteryClient, LipoModel, Utils
from config.settings import DCDC_CONFIG, BATTERY_CONFIG
from controllers.socketio_controller import emit_event

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class RenogyService:
    def __init__(self):
        # Initialize clients with correct callback registration
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

    def start(self):
        """Start both Renogy clients"""
        self.dcdc_client.start()
        self.battery_client.start()
        log.info("Renogy service started")

    def stop(self):
        """Stop both Renogy clients"""
        self.dcdc_client.stop()
        self.battery_client.stop()
        log.info("Renogy service stopped")

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