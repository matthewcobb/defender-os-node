"""
Main application entry point
"""
import logging
from quart import Quart
import socketio
from controllers.system_controller import system_bp
from controllers.gpio_controller import gpio_bp, monitor_reverse_light, is_reversing
from controllers.socketio_controller import sio, sio_bp, update_last_state
from utils.middleware import add_cors_headers
from services.renogy_service import monitor_renogybt, stop_renogybt
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

# Store background tasks for better management
background_tasks = []

# Connect to Renogy devices on startup
@app.before_serving
async def before_serving():
    """Setup tasks before the server starts"""
    # Configure asyncio for better performance on resource-constrained systems
    import asyncio
    try:
        # Increase event loop slow callback duration warning threshold
        # to account for Bluetooth operations which may be slow on Raspberry Pi
        loop = asyncio.get_event_loop()
        loop.slow_callback_duration = 2.0  # seconds (default is 0.1)
        log.info(f"Set slow callback duration warning threshold to 2.0 seconds")

        # On Linux/Raspberry Pi, try to optimize further
        import platform
        if platform.system() == 'Linux':
            # Try to set a higher priority for the main process
            import os
            try:
                os.nice(-10)  # Higher priority (lower nice value) for main process
                log.info("Set main process to higher priority")
            except:
                log.warning("Could not set process priority")
    except Exception as e:
        log.warning(f"Could not configure event loop: {e}")

    log.info("Starting background tasks...")

    # Start Renogy service as a background task
    renogy_task = app.add_background_task(monitor_renogybt)
    background_tasks.append(renogy_task)
    log.info("Renogy monitoring task started")

    # Initialize the GPIO state in the Socket.IO controller
    update_last_state('gpio', {'is_reversing': is_reversing})

    # Start reverse light monitoring in background
    gpio_task = app.add_background_task(monitor_reverse_light)
    background_tasks.append(gpio_task)
    log.info("GPIO monitoring task started")

    log.info("Server startup complete")

# Cleanup on shutdown
@app.after_serving
async def after_serving():
    """Cleanup tasks after the server stops"""
    log.info("Server shutting down, cleaning up resources...")

    # Cancel all background tasks
    log.info(f"Cancelling {len(background_tasks)} background tasks...")
    for task in background_tasks:
        if not task.cancelled():
            task.cancel()
            try:
                await task
            except:
                pass  # Task was cancelled, ignore exceptions

    # Stop the Renogy service explicitly
    log.info("Stopping Renogy service...")
    await stop_renogybt()

    log.info("Cleanup complete")

# Create the final ASGI application for gunicorn to use
# This must be named 'application' to match your gunicorn configuration
application = socketio.ASGIApp(sio, app)