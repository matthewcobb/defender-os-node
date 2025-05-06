"""
SocketIO controller for real-time data streaming
"""
import json
import logging
import socketio
import asyncio
from quart import Blueprint
import time

# Configure logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

# Create Socket.IO server with improved configuration
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True,
    ping_timeout=40,           # Increased from 30
    ping_interval=20,          # Increased from 15
    max_http_buffer_size=1e6,  # 1 MB max message size
    allow_upgrades=True,
    http_compression=True      # Compress HTTP responses
)

# Create Blueprint for Socket.IO routes
sio_bp = Blueprint('socketio', __name__)

# Store client connection information
connected_clients = {}

# Store last known state for each data type to send to new connections
last_state = {
    'renogy': None,
    'gpio': {
        'is_reversing': False
    },
    'system': {
        'overall_status': 'not_started',
        'logs': [],
        'current_step': None,
        'error': None
    },
    'wifi': None
}

@sio.event
async def connect(sid, environ):
    """Handle new client connection"""
    client_ip = environ.get('REMOTE_ADDR', 'unknown')
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    # Store client info
    connected_clients[sid] = {
        'ip': client_ip,
        'connected_at': timestamp,
        'last_activity': timestamp
    }

    log.info(f"New SocketIO connection: {sid} from IP: {client_ip}")

    # Send initial state to the new client
    for data_type, data in last_state.items():
        if data:
            await sio.emit(f"{data_type}:initial_state", data, room=sid)
            await asyncio.sleep(0.1)  # Small delay between messages to prevent flooding

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    client_info = connected_clients.get(sid, {'ip': 'unknown'})
    log.warning(f"SocketIO client disconnected: {sid} from IP: {client_info['ip']}")

    # Clean up client info
    if sid in connected_clients:
        del connected_clients[sid]

@sio.event
async def ping(sid, data):
    """Handle ping messages"""
    # Update last activity time
    if sid in connected_clients:
        connected_clients[sid]['last_activity'] = time.strftime('%Y-%m-%d %H:%M:%S')

    # Send pong response
    await sio.emit('pong', {}, room=sid)

@sio.event
async def system_request_update(sid, data):
    """Handle system update requests"""
    from services.system_service import start_system_update
    log.info(f"System update requested by client: {sid}")
    await start_system_update()

async def emit_event(event_type, event_name, data):
    """
    Emit an event to all connected clients

    Args:
        event_type (str): Type of event (e.g., 'renogy', 'gpio')
        event_name (str): Name of the event (e.g., 'data_update')
        data (dict): Data to send
    """
    # Update last known state
    update_last_state(event_type, data)

    # Log active connections before broadcasting
    active_clients = len(connected_clients)
    log.debug(f"Broadcasting {event_type}:{event_name} to {active_clients} clients")

    try:
        # Emit the event to all clients
        await sio.emit(f"{event_type}:{event_name}", data)
    except Exception as e:
        log.error(f"Error emitting {event_type}:{event_name}: {str(e)}")

def update_last_state(state_type, data):
    """Update the last known state for a specific event type"""
    last_state[state_type] = data


