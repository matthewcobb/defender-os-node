"""
Service for handling Renogy device connections and data retrieval
"""
import logging
import asyncio
import time
from datetime import datetime, timedelta
import platform
from renogybt import RoverClient, BatteryClient, LipoModel, Utils
from config.settings import DCDC_CONFIG, BATTERY_CONFIG, POLL_INTERVAL
from controllers.socketio_controller import emit_event

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
        self.start_time = None
        self.successful_polls = 0
        self.failed_polls = 0
        self.last_poll_time = None
        self.error_counts = {'rng_ctrl': 0, 'rng_batt': 0}
        self.reconnect_counts = {'rng_ctrl': 0, 'rng_batt': 0}

        # Log system information at startup
        log.info(f"🖥️  System: {platform.system()} {platform.release()} on {platform.machine()}")
        log.info(f"🐍 Python: {platform.python_version()}")

    async def start(self):
        self.should_run = True
        self.start_time = datetime.now()
        log.info(f"🚀 Starting Renogy service at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log.info(f"⏱️  Poll interval: {POLL_INTERVAL} seconds")

        # Initialize clients with configuration from settings.py
        client_configs = {
            'rng_ctrl': DCDC_CONFIG,
            'rng_batt': BATTERY_CONFIG
        }

        # Log device configurations
        for device_type, config in client_configs.items():
            log.info(f"📱 {device_type} configuration:")
            for key, value in config.items():
                log.info(f"   {key}: {value}")

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
                log.info("🔌 Connecting to Renogy devices...")
                connection_results = {}
                for device_type, client in self.clients.items():
                    connection_results[device_type] = await client.connect()
                    if connection_results[device_type]:
                        log.info(f"✅ Connected to {device_type}")
                    else:
                        log.error(f"❌ Failed to connect to {device_type}")
                        self.reconnect_counts[device_type] += 1

                # Check if all connections were successful
                if all(connection_results.values()):
                    log.info("✅ Successfully connected to all Renogy devices")

                    # Polling phase
                    try:
                        poll_start_time = datetime.now()
                        log.info(f"📊 Starting polling at {poll_start_time.strftime('%H:%M:%S')}")

                        while self.should_run:
                            # Track start time of this polling cycle
                            cycle_start = time.time()
                            self.last_poll_time = datetime.now()

                            poll_success = True
                            # Run read tasks sequentially instead of concurrently
                            # to avoid overloading the Bluetooth controller
                            for device_type, client in self.clients.items():
                                log.info(f"📡 Reading data from {device_type}...")
                                try:
                                    success = await client.read_all_data()
                                    if not success:
                                        log.error(f"❌ Failed to read data from {device_type}")
                                        poll_success = False
                                        self.failed_polls += 1
                                        self.error_counts[device_type] += 1
                                    else:
                                        log.info(f"✅ Successfully read data from {device_type}")
                                except Exception as e:
                                    log.error(f"❌ Error reading from {device_type}: {e}")
                                    poll_success = False
                                    self.failed_polls += 1
                                    self.error_counts[device_type] += 1

                                # Add a small delay between device reads
                                await asyncio.sleep(1)

                            # Log poll success or failure
                            if poll_success:
                                self.successful_polls += 1

                            # Calculate time spent on this polling cycle
                            cycle_duration = time.time() - cycle_start

                            # If the poll was very quick, log a warning as it might indicate a problem
                            if cycle_duration < 1.0:
                                log.warning(f"⚠️ Poll cycle was very quick ({cycle_duration:.2f}s) - possible Bluetooth issue")

                            # Log polling statistics periodically
                            if (self.successful_polls + self.failed_polls) % 10 == 0:
                                uptime = datetime.now() - self.start_time
                                uptime_str = str(uptime).split('.')[0]  # Remove microseconds
                                success_rate = 0
                                if self.successful_polls + self.failed_polls > 0:
                                    success_rate = (self.successful_polls / (self.successful_polls + self.failed_polls)) * 100

                                log.info(f"📊 Polling stats - Uptime: {uptime_str}, Success: {self.successful_polls}, " +
                                         f"Failed: {self.failed_polls}, Rate: {success_rate:.1f}%")
                                log.info(f"📊 Error counts - rng_ctrl: {self.error_counts['rng_ctrl']}, " +
                                         f"rng_batt: {self.error_counts['rng_batt']}")

                            # Calculate how long to wait for next poll
                            remaining_wait = POLL_INTERVAL - cycle_duration
                            if remaining_wait > 0:
                                log.info(f"⏱️ Waiting {remaining_wait:.1f}s until next poll")
                                await asyncio.sleep(remaining_wait)
                            else:
                                log.warning(f"⚠️ Poll cycle took longer ({cycle_duration:.1f}s) than poll interval ({POLL_INTERVAL}s)")
                                # Still add a small delay to avoid tight loops
                                await asyncio.sleep(0.5)

                    except asyncio.CancelledError:
                        raise  # Allow cancellation to propagate
                    except Exception as e:
                        log.error(f"❌ Error during polling phase: {e}")
                        import traceback
                        log.error(f"Traceback: {traceback.format_exc()}")
                else:
                    # Log which devices failed to connect
                    for device_type, connected in connection_results.items():
                        if not connected:
                            log.error(f"❌ Failed to connect to {device_type}: {self.clients[device_type].client_config.get('alias')}")
                            self.reconnect_counts[device_type] += 1

                    # Wait before retrying connection
                    retry_seconds = 5
                    log.info(f"⏱️ Waiting {retry_seconds}s before reconnection attempt")
                    await asyncio.sleep(retry_seconds)
            except Exception as e:
                log.error(f"❌ Error during connection attempt: {e}")
                import traceback
                log.error(f"Traceback: {traceback.format_exc()}")
                log.info("⏱️ Waiting 5s before retry")
                await asyncio.sleep(5)
            finally:
                # Ensure we disconnect clients if loop is exiting but service is still running
                if self.should_run:
                    await self._disconnect_clients()

        # Final cleanup when service is stopping
        await self._disconnect_clients()
        log.info("🛑 Renogy service stopped")

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
        log.error(f"❌ Renogy client error ({device_type}): {error}")

        # Track errors by device
        if device_type in self.error_counts:
            self.error_counts[device_type] += 1

        # Analyze error patterns
        if "timeout" in str(error).lower():
            log.error(f"⏱️ Timeout detected for {device_type}")
            # Check when the last successful poll was
            if self.last_poll_time:
                time_since_poll = datetime.now() - self.last_poll_time
                log.error(f"⏱️ Time since last poll attempt: {time_since_poll.total_seconds():.1f}s")

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
