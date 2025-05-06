/**
 * Socket.IO service for real-time data
 * This service handles all Socket.IO connections for the application
 */

import { io, Socket } from 'socket.io-client';
import mitt from 'mitt';

// Event bus for Socket.IO events
type Events = {
  [key: string]: any;
  connected: boolean;
};

export const socketEvents = mitt<Events>();

// Connection state tracking
let socket: Socket | null = null;
let isInitialized = false;
let reconnecting = false;
let heartbeatInterval: number | null = null;
let reconnectionAttempts = 0;

/**
 * Initialize the Socket.IO connection
 */
export function initSocketIO() {
  if (isInitialized) {
    console.log('[Socket.IO] Already initialized, skipping redundant initialization');
    return;
  }

  console.log('[Socket.IO] Initializing connection');

  // Get the server URL from the current location
  const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
  const host = window.location.hostname;
  const port = '5000'; // Same port as your Python backend

  const socketUrl = `${protocol}://${host}:${port}`;
  console.log(`[Socket.IO] Connecting to: ${socketUrl}`);

  // Create Socket.IO connection with improved reconnection parameters
  socket = io(socketUrl, {
    reconnection: true,
    reconnectionAttempts: 5,      // Limit reconnection attempts to 5
    reconnectionDelay: 2000,      // Wait 2 seconds before first retry
    reconnectionDelayMax: 10000,  // Maximum delay between retries
    timeout: 10000,               // Shorter connection timeout
    transports: ['polling', 'websocket'],
    withCredentials: false,
    path: '/socket.io',
  });

  // Connection event handlers
  socket.on('connect', () => {
    const timestamp = new Date().toISOString();
    console.log(`[Socket.IO] [${timestamp}] Connected successfully`);
    socketEvents.emit('connected', true);
    reconnecting = false;
    reconnectionAttempts = 0;

    // Start heartbeat when connected
    startHeartbeat();
  });

  socket.on('disconnect', (reason) => {
    const timestamp = new Date().toISOString();
    console.log(`[Socket.IO] [${timestamp}] Disconnected: ${reason}`);
    socketEvents.emit('connected', false);

    // Stop heartbeat on disconnect
    stopHeartbeat();

    // If the disconnection wasn't initiated by us and we aren't already reconnecting
    if (reason !== 'io client disconnect' && !reconnecting) {
      reconnecting = true;
      reconnectionAttempts++;
    }
  });

  socket.on('connect_error', (error) => {
    const timestamp = new Date().toISOString();
    console.error(`[Socket.IO] [${timestamp}] Connection error:`, error);
    socketEvents.emit('connected', false);
    reconnectionAttempts++;
  });

  // Set up custom event handler for all events
  socket.onAny((event, ...args) => {
    // Re-emit the event to our event bus
    socketEvents.emit(event, args[0]);
  });

  // Set up the default error handler
  socket.on('error', (error) => {
    const timestamp = new Date().toISOString();
    console.error(`[Socket.IO] [${timestamp}] Error:`, error);
  });

  // Handle pong response from server
  socket.on('pong', () => {
    const timestamp = new Date().toISOString();
    console.log(`[Socket.IO] [${timestamp}] Received pong from server`);
  });

  isInitialized = true;
}

/**
 * Start heartbeat mechanism to keep connection alive
 */
function startHeartbeat() {
  if (heartbeatInterval) return;

  // Send ping every 30 seconds to keep connection alive
  heartbeatInterval = window.setInterval(() => {
    if (socket?.connected) {
      console.log(`[Socket.IO] Sending heartbeat ping`);
      sendMessage('ping');
    }
  }, 30000);
}

/**
 * Stop heartbeat mechanism
 */
function stopHeartbeat() {
  if (heartbeatInterval) {
    window.clearInterval(heartbeatInterval);
    heartbeatInterval = null;
  }
}

/**
 * Send a message through Socket.IO
 */
export function sendMessage(event: string, data?: any): boolean {
  if (!socket || !socket.connected) {
    return false;
  }

  socket.emit(event, data || {});
  return true;
}

/**
 * Disconnect the Socket.IO connection
 */
export function disconnect(): void {
  if (socket) {
    console.log('[Socket.IO] Disconnecting');
    socket.disconnect();
    socket = null;
  }

  stopHeartbeat();
  isInitialized = false;
  reconnecting = false;
}

/**
 * Get the current connection state
 */
export function isConnected(): boolean {
  return socket?.connected || false;
}

/**
 * Get the current reconnection attempts count
 */
export function getReconnectionAttempts(): number {
  return reconnectionAttempts;
}

/**
 * Send a ping to keep the connection alive
 */
export function sendPing(): void {
  console.log('[Socket.IO] Manually sending ping');
  sendMessage('ping');
}

/**
 * Force a reconnection
 */
export function forceReconnect(): void {
  if (!socket) {
    console.log('[Socket.IO] No socket to reconnect, initializing');
    initSocketIO();
    return;
  }

  console.log('[Socket.IO] Forcing reconnection');

  // Disconnect current socket
  if (socket.connected) {
    socket.disconnect();
  }

  // Reset the socket and reconnect
  socket.connect();
}