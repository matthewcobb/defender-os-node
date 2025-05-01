"""
Service for handling Renogy device connections and data retrieval
"""
import logging
import asyncio
from renogybt import RoverClient, BatteryClient, LipoModel
from config.settings import DCDC_CONFIG, BATTERY_CONFIG, DEVELOPMENT_MODE
from controllers.socketio_controller import emit_event, update_last_state

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Mock data for development mode
MOCK_RENOGY_DATA = [
    {
        "function": "READ",
        "model": "RBC50D1S-G1",
        "device_id": 96,
        "battery_percentage": 100,
        "battery_voltage": 13.4,
        "battery_current": 20,
        "battery_temperature": 25,
        "controller_temperature": 21,
        "load_status": "off",
        "load_voltage": 12.5,
        "load_current": 0.0,
        "load_power": 10,
        "pv_voltage": 18.7,
        "pv_current": 0.45,
        "pv_power": 10,
        "max_charging_power_today": 200,
        "max_discharging_power_today": 0,
        "charging_amp_hours_today": 4,
        "discharging_amp_hours_today": 0,
        "power_generation_today": 54,
        "power_consumption_today": 0,
        "power_generation_total": 39664,
        "charging_status": "mppt",
        "battery_type": "lithium"
    },
    {
        "function": "READ",
        "cell_count": 4,
        "cell_voltage_0": 3.3,
        "cell_voltage_1": 3.3,
        "cell_voltage_2": 3.3,
        "cell_voltage_3": 3.3,
        "sensor_count": 4,
        "temperature_0": 11.0,
        "temperature_1": 11.0,
        "temperature_2": 11.0,
        "temperature_3": 11.0,
        "current": 0.48,
        "voltage": 13.4,
        "time_remaining_to_charge": "1hr 40mins",
        "time_remaining_to_empty": "1hr 40mins",
        "pv_power": 10,
        "load_power": 10,
        "remaining_charge": 40,
        "capacity": 99.99,
        "model": "RBT100LFP12S-G",
        "device_id": 247
    }
]

# Create clients
dcdc_client = RoverClient(DCDC_CONFIG)
battery_client = BatteryClient(BATTERY_CONFIG)

# Background task for periodic data collection
_update_task = None
_is_running = False
_update_interval = 5  # seconds

async def connect():
    """Connect to Renogy devices"""
    if not DEVELOPMENT_MODE:
        await dcdc_client.connect()
        await battery_client.connect()
    else:
        log.info("Development mode enabled - using mock data")

async def fetch_data():
    """Fetch data from Renogy devices"""
    if DEVELOPMENT_MODE:
        # Return mock data in development mode
        return MOCK_RENOGY_DATA, 200

    # Normal operation - connect to real devices
    await connect()

    if not dcdc_client.is_connected or not battery_client.is_connected:
        logging.error("RenogyBT not connected")
        return {"error": "RenogyBT not connected"}, 500

    # Compile data request
    if dcdc_client.latest_data and battery_client.latest_data:
        try:
            data = LipoModel(dcdc_client.latest_data, battery_client.latest_data).calculate()
            logging.info(data)
            return data, 200
        except Exception as e:
            logging.error(e)
            return {"error": str(e)}, 500
    else:
        logging.error("No data found")
        return {"error": "No data found!"}, 500

async def broadcast_renogy_data():
    """Broadcast current Renogy data to all Socket.IO clients"""
    await emit_event('renogy', 'data_update', update_status)

async def update_renogy_data(new_data=None):
    """Update Renogy data and broadcast to Socket.IO clients"""
    if new_data:
        update_last_state('renogy', new_data)

    # Broadcast the updated status
    await emit_event('renogy', 'data_update', new_data)

async def start_periodic_updates():
    """Start periodic data collection and broadcasting"""
    global _update_task, _is_running

    if _is_running:
        return

    _is_running = True
    _update_task = asyncio.create_task(_periodic_update())
    log.info("Started periodic Renogy data updates")

async def stop_periodic_updates():
    """Stop periodic data collection"""
    global _update_task, _is_running

    _is_running = False

    if _update_task:
        _update_task.cancel()
        try:
            await _update_task
        except asyncio.CancelledError:
            pass
        _update_task = None
        log.info("Stopped periodic Renogy data updates")

async def _periodic_update():
    """Periodically fetch and broadcast Renogy data"""
    while _is_running:
        try:
            data, status = await fetch_data()

            if status == 200:
                # Format data for broadcasting
                if isinstance(data, list) and len(data) >= 2:
                    renogy_data = {
                        'solar': data[0],
                        'battery': data[1]
                    }
                    # Broadcast data to all connected clients using Socket.IO
                    await emit_event('renogy', 'data_update', renogy_data)
        except Exception as e:
            log.error(f"Error in periodic Renogy update: {e}")

        # Wait for next update interval
        await asyncio.sleep(_update_interval)

def set_update_interval(seconds):
    """Change the update interval for Renogy data"""
    global _update_interval
    _update_interval = max(1, seconds)  # Minimum 1 second