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
from services.splash_service import remove_splash_screen

# Create Blueprint for system routes
system_bp = Blueprint('system', __name__)

@system_bp.route('/cpu_temp', methods=['GET'])
async def cpu_temp():
    """Get CPU temperature"""
    return get_cpu_temperature()

@system_bp.route('/close_kiosk', methods=['POST'])
async def close_kiosk_browser():
    """Close Chrome/Chromium kiosk browser"""
    return await close_kiosk()

@system_bp.route('/remove_splash', methods=['POST'])
async def remove_splash():
    """Remove the boot splash screen"""
    return remove_splash_screen()