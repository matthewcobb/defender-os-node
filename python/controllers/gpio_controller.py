"""
GPIO controller for monitoring reverse light and other GPIO functions
"""
import time
import logging
import asyncio
from quart import Blueprint, jsonify
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

# GPIO setup
reverse_sensor = None

# Try to initialize GPIO
if not DEVELOPMENT_MODE:
    try:
        # For Raspberry Pi 5, we need to use the lgpio pin factory
        import lgpio
        from gpiozero import DigitalInputDevice
        from gpiozero import Device
        from gpiozero.pins.lgpio import LGPIOFactory

        # Set the default pin factory to lgpio
        Device.pin_factory = LGPIOFactory()
        log.info("Using gpiozero with lgpio pin factory for Raspberry Pi 5")

        # Initialize with lgpio pin factory
        # Using pull-up resistor so the pin is normally HIGH when not in reverse
        reverse_sensor = DigitalInputDevice(
            REVERSE_PIN,
            pull_up=True  # Use pull-up resistor (active state will be LOW by default)
        )

        # Log the initial state of the pin
        initial_pin_state = reverse_sensor.is_active
        initial_reverse_state = not initial_pin_state

        log.info(f"GPIO reverse sensor initialized on pin BCM{REVERSE_PIN} with pull-up")
        log.info(f"Initial reverse sensor pin state: {'ACTIVE (LOW)' if initial_pin_state else 'INACTIVE (HIGH)'}")
        log.info(f"Initial car reverse state: {'IN REVERSE' if initial_reverse_state else 'NOT IN REVERSE'}")

        # Use the initial state to initialize our is_reversing state
        is_reversing = initial_reverse_state
        log.info(f"Setting initial reversing state to: {is_reversing}")

    except Exception as e:
        log.error(f"Failed to initialize GPIO: {e}")
        log.warning("Using fallback mode - no GPIO functionality")
        is_reversing = False
else:
    is_reversing = False

def read_gpio_state():
    """Read the current state of the reverse light GPIO pin"""
    if DEVELOPMENT_MODE or reverse_sensor is None:
        # For development without actual GPIO hardware
        return False

    try:
        # Invert the value from the sensor to get the correct reversing state
        # When pin is active (LOW), the car is NOT in reverse
        # When pin is inactive (HIGH), the car IS in reverse
        return not reverse_sensor.is_active
    except Exception as e:
        log.error(f"Error reading GPIO: {e}")
        return False

async def monitor_reverse_light():
    """Monitor the reverse light GPIO pin for changes"""
    global is_reversing, potential_new_state, potential_state_start_time

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