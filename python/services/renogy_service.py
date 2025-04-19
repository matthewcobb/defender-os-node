"""
Service for handling Renogy device connections and data retrieval
"""
import logging
from renogybt import RoverClient, BatteryClient, LipoModel
from config.settings import DCDC_CONFIG, BATTERY_CONFIG

# Create clients
dcdc_client = RoverClient(DCDC_CONFIG)
battery_client = BatteryClient(BATTERY_CONFIG)

async def connect():
    """Connect to Renogy devices"""
    await dcdc_client.connect()
    await battery_client.connect()

async def fetch_data():
    """Fetch data from Renogy devices"""
    # Ensure connections
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