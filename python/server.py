"""
DEPRECATED: This file is maintained for backwards compatibility.
Please use main.py for new development.

This file now just imports from the restructured modules.
"""
from quart import Quart, jsonify, Response
import logging

# Import from new structure
from services.renogy_service import dcdc_client, battery_client, connect, fetch_data
from services.system_service import (
    get_cpu_temperature,
    close_kiosk,
    start_system_update,
    get_update_status,
    update_status
)
from utils.middleware import add_cors_headers

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('quart.app')
log.setLevel(logging.INFO)

# Create app
app = Quart(__name__)

# Add CORS headers to all responses
@app.after_request
async def cors_middleware(response):
    return await add_cors_headers(response)

@app.before_serving
async def before_serving():
    await connect()

async def fetch_renogy_data():
    return await fetch_data()

@app.route('/renogy_data', methods=['GET'])
async def dcdc_status():
    return await fetch_renogy_data()

@app.route('/cpu_temp', methods=['GET'])
def cpu_temp():
    return get_cpu_temperature()

@app.route('/update_system', methods=['POST'])
async def update_system():
    return await start_system_update()

@app.route('/update_status', methods=['GET'])
async def get_update_status_route():
    return get_update_status()

@app.route('/close_kiosk', methods=['POST'])
async def close_kiosk_route():
    return await close_kiosk()

if __name__ == '__main__':
    app.run(debug=True)