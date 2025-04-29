"""
Main application entry point
"""
import logging
from quart import Quart
import socketio
from controllers.renogy_controller import renogy_bp
from controllers.system_controller import system_bp
from controllers.gpio_controller import gpio_bp, monitor_reverse_light, is_reversing
from controllers.socketio_controller import sio, sio_bp, update_last_state
from utils.middleware import add_cors_headers
from services.renogy_service import connect as connect_renogy
from services.renogy_service import start_periodic_updates
from config.settings import DEBUG, HOST, PORT

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('quart.app')
log.setLevel(logging.INFO)

# Create Quart app
app = Quart(__name__)

# Register blueprints
app.register_blueprint(renogy_bp)
app.register_blueprint(system_bp)
app.register_blueprint(gpio_bp)
app.register_blueprint(sio_bp)

# Add CORS middleware
app.after_request(add_cors_headers)

# Connect to Renogy devices on startup
@app.before_serving
async def before_serving():
    # Connect to devices
    await connect_renogy()

    # Initialize the GPIO state in the Socket.IO controller
    update_last_state('gpio', {'is_reversing': is_reversing})

    # Start reverse light monitoring in background
    app.add_background_task(monitor_reverse_light)

    # Start periodic Renogy data updates
    app.add_background_task(start_periodic_updates)

# Create the final ASGI application for gunicorn to use
# This must be named 'application' to match your gunicorn configuration
application = socketio.ASGIApp(sio, app)