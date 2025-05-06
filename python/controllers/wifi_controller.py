"""
Controller for WiFi-related endpoints
"""
import asyncio
import logging
from quart import Blueprint, jsonify, request
from services.wifi_service import (
    get_wifi_status,
    scan_networks,
    connect_to_network,
    disconnect_network
)
from controllers.socketio_controller import emit_event

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Create Blueprint for wifi routes
wifi_bp = Blueprint('wifi', __name__)

# Last known WiFi status
last_wifi_status = None

@wifi_bp.route('/wifi/status', methods=['GET'])
async def wifi_status():
    """Get WiFi connection status"""
    return jsonify(get_wifi_status())

@wifi_bp.route('/wifi/scan', methods=['POST'])
async def scan_wifi():
    """Scan for available WiFi networks"""
    scan_result = await scan_networks()
    return jsonify(scan_result)

@wifi_bp.route('/wifi/connect', methods=['POST'])
async def connect_wifi():
    """Connect to a WiFi network"""
    data = await request.get_json()
    ssid = data.get('ssid')
    password = data.get('password', '')

    if not ssid:
        return jsonify({
            'success': False,
            'error': 'SSID is required'
        }), 400

    connect_result = await connect_to_network(ssid, password)

    # Always emit the current status via websocket, regardless of success
    updated_status = get_wifi_status()
    await emit_event('wifi', 'status_update', updated_status)

    return jsonify(connect_result)

@wifi_bp.route('/wifi/disconnect', methods=['POST'])
async def disconnect_wifi():
    """Disconnect from WiFi network"""
    disconnect_result = await disconnect_network()

    # Always emit the current status via websocket, regardless of success
    updated_status = get_wifi_status()
    await emit_event('wifi', 'status_update', updated_status)

    return jsonify(disconnect_result)

async def monitor_wifi_status():
    """Monitor WiFi status and emit updates via websocket"""
    global last_wifi_status

    log.info("Starting WiFi status monitoring...")

    while True:
        try:
            # Get current WiFi status
            current_status = get_wifi_status()

            # If status changed, emit an update
            if last_wifi_status != current_status:
                log.info(f"WiFi status changed: {current_status}")
                await emit_event('wifi', 'status_update', current_status)
                last_wifi_status = current_status

            # Wait before checking again - still check frequently but only emit on changes
            await asyncio.sleep(5)  # Increased from 2 to 5 seconds to reduce overhead

        except Exception as e:
            log.error(f"Error in WiFi status monitoring: {e}")
            await asyncio.sleep(30)  # Wait longer after an error