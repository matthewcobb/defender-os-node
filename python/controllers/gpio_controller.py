from quart import Blueprint, jsonify, websocket
import asyncio
import logging
import json
import random
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('gpio_controller')

# Simple flag to control whether to use real or simulated GPIO
# Set to True for development/debugging on systems without GPIO hardware
DEBUG_GPIO = True

try:
    import gpiod
    log.info("Using real gpiod module")
except ImportError as e:
    log.error(f"Failed to import gpiod: {e}")
    log.warning("Forcing DEBUG_GPIO mode")
    DEBUG_GPIO = True

gpio_bp = Blueprint('gpio', __name__, url_prefix='/gpio')

# Default GPIO pin for reverse light detection
REVERSE_PIN = 7  # GPIO pin number

# Store active WebSocket connections
active_connections = set()

# For mock mode
mock_reverse_value = False

# GPIO setup
chip = None
reverse_line = None

if not DEBUG_GPIO:
    try:
        chip = gpiod.Chip('gpiochip0')  # Default chip on Raspberry Pi
        reverse_line = chip.get_line(REVERSE_PIN)
        reverse_line.request(consumer="defender-os", type=gpiod.LINE_REQ_DIR_IN, flags=gpiod.LINE_REQ_FLAG_ACTIVE_LOW)
        log.info(f"GPIO reverse sensor initialized on pin {REVERSE_PIN}")
    except Exception as e:
        log.error(f"Failed to initialize GPIO reverse sensor: {e}")
        log.warning("Forcing DEBUG_GPIO mode")
        DEBUG_GPIO = True

# State tracking
is_reversing = False
debounce_time = 0.1  # seconds
potential_new_state = None
potential_state_time = 0

async def broadcast_message(message_data):
    """Send a message to all active WebSocket connections"""
    message = json.dumps(message_data)
    current_time = time.time()

    # Clean up dead connections while sending messages
    for connection in list(active_connections):
        try:
            await connection.send(message)
            # Update last active timestamp
            connection.last_active = current_time
        except Exception as e:
            log.error(f"Error sending to WebSocket: {e}")
            # Remove dead connection
            active_connections.discard(connection)

def read_gpio_state():
    """Read the current GPIO state, handling both real and debug modes"""
    global mock_reverse_value

    if DEBUG_GPIO:
        # Randomly change mock state occasionally (5% chance)
        if random.random() < 0.05:
            mock_reverse_value = not mock_reverse_value
        return mock_reverse_value
    else:
        # Use real GPIO
        return bool(reverse_line.get_value())

async def monitor_reverse_light():
    """Background task to monitor the reverse light status and notify clients"""
    global is_reversing, potential_new_state, potential_state_time

    log.info("Starting reverse light monitoring")

    while True:
        try:
            current_time = time.time()
            raw_state = read_gpio_state()

            # Debounce logic
            if raw_state != is_reversing:
                if potential_new_state is None:
                    # First detection of a change
                    potential_new_state = raw_state
                    potential_state_time = current_time
                elif raw_state == potential_new_state:
                    # Same reading as potential - check if it's been stable long enough
                    if current_time - potential_state_time >= debounce_time:
                        # State has been stable for debounce period - accept the change
                        is_reversing = potential_new_state
                        log.info(f"Reverse state changed to: {is_reversing}")
                        potential_new_state = None

                        # Notify all connected clients
                        await broadcast_message({
                            "event": "reverse_state_change",
                            "data": {
                                "is_reversing": is_reversing
                            }
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

@gpio_bp.websocket('/events')
async def gpio_events():
    """WebSocket endpoint for real-time GPIO events"""
    try:
        current_connection = websocket._get_current_object()
        # Register new connection with timestamp
        active_connections.add(current_connection)
        setattr(current_connection, 'last_active', time.time())

        # Send initial state
        await websocket.send(json.dumps({
            "event": "initial_state",
            "data": {
                "is_reversing": is_reversing
            }
        }))

        # Keep connection alive
        while True:
            # Wait for messages and keep connection alive
            data = await websocket.receive()

            # Update the last active timestamp
            current_connection.last_active = time.time()

            # Handle ping messages from client
            try:
                message = json.loads(data)
                if message.get('type') == 'ping':
                    # Respond with pong
                    await websocket.send(json.dumps({"type": "pong"}))
            except:
                # Not a JSON message or not a ping, just keep connection alive
                pass

    except asyncio.CancelledError:
        # Normal disconnection
        pass
    except Exception as e:
        log.error(f"WebSocket error: {e}")
    finally:
        # Remove connection when done
        active_connections.discard(current_connection)

@gpio_bp.route('/status', methods=['GET'])
async def gpio_status():
    """Get current status of GPIO pins"""
    return jsonify({
        "is_reversing": is_reversing,
        "reverse_pin": REVERSE_PIN
    })