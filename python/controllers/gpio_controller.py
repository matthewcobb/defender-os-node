"""
GPIO controller for monitoring reverse light and other GPIO functions
"""
import time
import logging
import asyncio
from quart import Blueprint, jsonify
import RPi.GPIO as GPIO
from config.settings import REVERSE_PIN, DEVELOPMENT_MODE
from controllers.socketio_controller import emit_event

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Create blueprint
gpio_bp = Blueprint('gpio', __name__, url_prefix='/gpio')

# Track current reversing state
is_reversing = False

# Track state change variables
potential_new_state = None
potential_state_start_time = 0
STATE_CHANGE_THRESHOLD = 0.5  # seconds

def initialize_gpio():
    """Initialize GPIO settings"""
    if not DEVELOPMENT_MODE:
        try:
            log.info(f"Initializing GPIO on pin {REVERSE_PIN}")
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(REVERSE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            log.info("GPIO setup completed successfully")
            return True
        except Exception as e:
            log.error(f"GPIO setup error: {e}")
            return False
    return True

def read_gpio_state():
    """Read the current state of the reverse light GPIO pin"""
    if DEVELOPMENT_MODE:
        # For development without actual GPIO hardware
        return False

    try:
        return GPIO.input(REVERSE_PIN) == 1
    except Exception as e:
        log.error(f"Error reading GPIO: {e}")
        return False

async def monitor_reverse_light():
    """Monitor the reverse light GPIO pin for changes"""
    global is_reversing, potential_new_state, potential_state_start_time

    # Initialize GPIO at the start of monitoring
    if not initialize_gpio():
        log.error("Failed to initialize GPIO, monitoring will not work")
        return

    log.info(f"Starting reverse light monitoring on pin {REVERSE_PIN}")

    while True:
        try:
            # Read current state
            current_reading = read_gpio_state()

            # Debounce logic for reliable state detection
            if current_reading != is_reversing:
                # First time seeing a potential change
                if potential_new_state is None:
                    potential_new_state = current_reading
                    potential_state_start_time = time.time()
                # We're already tracking a potential change
                elif potential_new_state == current_reading:
                    # Check if it's been stable long enough
                    if time.time() - potential_state_start_time > STATE_CHANGE_THRESHOLD:
                        # Debounced state change confirmed
                        is_reversing = current_reading

                        log.info(f"Reverse light state changed: {is_reversing}")

                        # Broadcast state change using Socket.IO
                        await emit_event("gpio", "reverse_state_change", {
                            "is_reversing": is_reversing
                        })
                else:
                    # Reading disagrees with potential - reset potential
                    potential_new_state = None
            else:
                # Current reading matches current state - reset potential
                potential_new_state = None

        except Exception as e:
            log.error(f"Error in reverse light monitoring: {e}")

        # Small delay to prevent CPU hogging
        await asyncio.sleep(0.25)  # 250ms is plenty responsive for this use case