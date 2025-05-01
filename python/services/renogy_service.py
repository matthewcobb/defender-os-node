"""
Service for handling Renogy device connections and data retrieval
"""
import logging
import asyncio
from renogybt import RoverClient, BatteryClient, LipoModel, Utils
from config.settings import DCDC_CONFIG, BATTERY_CONFIG, POLL_INTERVAL
from controllers.socketio_controller import emit_event
from datetime import datetime

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class RenogyService:
    def __init__(self):
        self.clients = {}
        self.should_run = False
        self.device_data = {
            'rng_ctrl': {},
            'rng_batt': {},
            'combined': {}
        }

    async def start(self):
        self.should_run = True
        log.info("Starting Renogy service...")

        # Initialize clients with configuration from settings.py
        client_configs = {
            'rng_ctrl': DCDC_CONFIG,
            'rng_batt': BATTERY_CONFIG
        }

        # Create appropriate client based on type
        self.clients['rng_ctrl'] = RoverClient(
            client_config=client_configs['rng_ctrl'],
            on_data_callback=self.on_device_data_received,
            on_error_callback=self.on_error
        )

        self.clients['rng_batt'] = BatteryClient(
            client_config=client_configs['rng_batt'],
            on_data_callback=self.on_device_data_received,
            on_error_callback=self.on_error
        )

        while self.should_run:
            # Connection phase
            try:
                # Connect to all devices concurrently
                log.info("Connecting to Renogy devices...")
                connection_results = {}
                for device_type, client in self.clients.items():
                    connection_results[device_type] = await client.connect()

                # Check if all connections were successful
                if all(connection_results.values()):
                    log.info("Successfully connected to all Renogy devices")

                    # Polling phase
                    try:
                        while self.should_run:
                            # Run read tasks sequentially instead of concurrently
                            # to avoid overloading the Bluetooth controller
                            for device_type, client in self.clients.items():
                                log.info(f"Reading data from {device_type}...")
                                try:
                                    success = await client.read_all_data()
                                    if not success:
                                        log.error(f"Failed to read data from {device_type}")
                                except Exception as e:
                                    log.error(f"Error reading from {device_type}: {e}")

                                # Add a small delay between device reads
                                await asyncio.sleep(1)

                            # Wait for the next polling interval
                            await asyncio.sleep(POLL_INTERVAL)
                    except Exception as e:
                        log.error(f"Error during polling: {e}")
                else:
                    # Log which devices failed to connect
                    for device_type, connected in connection_results.items():
                        if not connected:
                            log.error(f"Failed to connect to {device_type}: {self.clients[device_type].client_config.get('alias')}")

                    # Wait before retrying connection
                    await asyncio.sleep(5)
            except Exception as e:
                log.error(f"Error during connection attempt: {e}")
                await asyncio.sleep(5)
            finally:
                # Ensure we disconnect clients if loop is exiting but service is still running
                if self.should_run:
                    await self._disconnect_clients()

        # Final cleanup when service is stopping
        await self._disconnect_clients()
        log.info("Renogy service stopped")

    async def _disconnect_clients(self):
        """Disconnect all clients"""
        for device_type, client in self.clients.items():
            try:
                await client.disconnect()
                log.info(f"Disconnected from {device_type}")
            except Exception as e:
                log.error(f"Error disconnecting from {device_type}: {e}")

    async def stop(self):
        """Stop the service"""
        log.info("Stopping Renogy service...")
        self.should_run = False

    def on_device_data_received(self, client, data):
        """Handle data received from any device client"""
        try:
            # Get device type directly from client configuration
            device_type = client.client_config.get('type', '').lower()

            # If type is not specified or invalid, use a fallback
            if not device_type or device_type not in self.device_data:
                log.warning(f"Unknown device type: {device_type}, using client name as fallback")
                device_type = client.__class__.__name__.lower().replace('client', '')
                if device_type == 'rover':
                    device_type = 'rng_ctrl'
                elif device_type == 'battery':
                    device_type = 'rng_batt'

            # Filter data if needed
            filtered_data = Utils.filter_fields(data, "")  # Blank for all fields

            # Store the filtered data
            self.device_data[device_type] = filtered_data

            # Update the model and emit combined data if we have both sets
            self._update_model_and_emit()

            log.debug(f"{device_type.upper()} data received: {client.client_config.get('alias')}")
        except Exception as e:
            log.error(f"Error processing {client.__class__.__name__} data: {e}")

    def _update_model_and_emit(self):
        """Update the LipoModel and emit combined data"""
        if not self.device_data['rng_ctrl'] or not self.device_data['rng_batt']:
            return  # Don't process until we have both

        # Update the model with latest data
        combined_data = LipoModel(self.device_data).calculate()

        if combined_data:
            # Store for later retrieval
            self.device_data['combined'] = combined_data

            # Emit to websocket clients
            asyncio.create_task(emit_event('renogy', 'data_update', combined_data))
            log.debug("Emitted combined Renogy data update")

    def on_error(self, client, error):
        """Handle errors from clients"""
        device_type = client.client_config.get('type', '').lower()
        log.error(f"Renogy client error ({device_type}): {error}")

        # Emit error to frontend
        error_data = {
            'device_type': device_type,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        }
        asyncio.create_task(emit_event('renogy', 'error', error_data))

    def get_latest_data(self):
        """Get the latest data for API requests"""
        return self.device_data

    async def set_dcdc_load(self, value):
        """Set the DCDC load state"""
        if 'rng_ctrl' not in self.clients or not self.clients['rng_ctrl'].connected:
            log.error("Cannot set load: DCDC not connected")
            return False

        return await self.clients['rng_ctrl'].set_load(value)

# Create a singleton instance
renogy_service = RenogyService()

# Export a function to get the main service coroutine for use with app.add_background_task
async def monitor_renogybt():
    """Main service coroutine - for use with app.add_background_task"""
    await renogy_service.start()

async def stop_renogybt():
    """Stop the service - used by app shutdown"""
    await renogy_service.stop()

def get_service():
    """Get the Renogy service instance"""
    return renogy_service
