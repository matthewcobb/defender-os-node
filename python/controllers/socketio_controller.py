"""
SocketIO controller for real-time data streaming
"""
import json
import logging
import socketio
from quart import Blueprint

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# Create Blueprint for Socket.IO routes
sio_bp = Blueprint('socketio', __name__)

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
    }
}

@sio.event
async def connect(sid, environ):
    """Handle new client connection"""
    log.info(f"New SocketIO connection: {sid}")

    # Send initial state to the new client
    for data_type, data in last_state.items():
        if data:
            await sio.emit(f"{data_type}:initial_state", data, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    log.info(f"SocketIO client disconnected: {sid}")

@sio.event
async def ping(sid, data):
    """Handle ping messages"""
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

    # Emit the event to all clients
    await sio.emit(f"{event_type}:{event_name}", data)

    log.debug(f"Emitted {event_type}:{event_name} event with data: {data}")

def update_last_state(state_type, data):
    """Update the last known state for a specific event type"""
    last_state[state_type] = data