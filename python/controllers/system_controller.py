"""
Controller for system-related endpoints
"""
from quart import Blueprint, jsonify
from services.system_service import (
    get_cpu_temperature,
    close_kiosk,
    start_system_update,
    get_update_status
)

# Create Blueprint for system routes
system_bp = Blueprint('system', __name__)

@system_bp.route('/cpu_temp', methods=['GET'])
async def cpu_temp():
    """Get CPU temperature"""
    return get_cpu_temperature()

@system_bp.route('/update_system', methods=['POST'])
async def update_system():
    """Initiate system update"""
    return await start_system_update()

@system_bp.route('/update_status', methods=['GET'])
async def update_status():
    """Get system update status"""
    return get_update_status()

@system_bp.route('/close_kiosk', methods=['POST'])
async def close_kiosk_browser():
    """Close Chrome/Chromium kiosk browser"""
    return await close_kiosk()