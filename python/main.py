"""
Main application entry point
"""
import logging
import asyncio
from quart import Quart, jsonify
import socketio
from controllers.system_controller import system_bp
from controllers.gpio_controller import gpio_bp, monitor_reverse_light, is_reversing
from controllers.socketio_controller import sio, sio_bp, update_last_state
from utils.middleware import add_cors_headers
from services.renogy_service import RenogyService
from config.settings import DEBUG, HOST, PORT

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('quart.app')
log.setLevel(logging.INFO)

# Create Quart app
app = Quart(__name__)

# Register blueprints
app.register_blueprint(system_bp)
app.register_blueprint(gpio_bp)
app.register_blueprint(sio_bp)

# Add CORS middleware
app.after_request(add_cors_headers)

# Create global Renogy service instance for app access
renogy_service = RenogyService()

# Connect to Renogy devices on startup
@app.before_serving
async def before_serving():
    """Setup tasks before the server starts"""
    # Start Renogy service
    log.info("Starting Renogy service...")
    renogy_service.start()

    # Add renogy_service to app context for access in other parts of the application
    app.renogy_service = renogy_service

    # Initialize the GPIO state in the Socket.IO controller
    update_last_state('gpio', {'is_reversing': is_reversing})

    # Start reverse light monitoring in background
    app.add_background_task(monitor_reverse_light)

    log.info("Server startup complete")

# Cleanup on shutdown
@app.after_serving
async def after_serving():
    """Cleanup tasks after the server stops"""
    log.info("Server shutting down, cleaning up resources...")

    # Stop the Renogy service
    await renogy_service.stop()

    log.info("Cleanup complete")

# Create the final ASGI application for gunicorn to use
# This must be named 'application' to match your gunicorn configuration
application = socketio.ASGIApp(sio, app)

# Route to get current Renogy data
@app.route('/api/renogy/status')
async def renogy_status():
    """Return current status of Renogy devices"""
    return jsonify(renogy_service.get_device_status())

@app.route('/api/renogy/data')
async def renogy_data():
    """Return latest Renogy data"""
    data = renogy_service.get_latest_data() or {'error': 'No data available yet'}
    return jsonify(data)