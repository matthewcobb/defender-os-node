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

/**
 * Initialize the Socket.IO connection
 */
export function initSocketIO() {
  if (isInitialized) return;

  // Get the server URL from the current location
  const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
  const host = window.location.hostname;
  const port = '5000'; // Same port as your Python backend

  const socketUrl = `${protocol}://${host}:${port}`;

  // Create Socket.IO connection with automatic reconnection
  socket = io(socketUrl, {
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 30000,
    timeout: 20000,
  });

  // Connection event handlers
  socket.on('connect', () => {
    console.log('Socket.IO connected');
    socketEvents.emit('connected', true);
    reconnecting = false;
  });

  socket.on('disconnect', (reason) => {
    console.log(`Socket.IO disconnected: ${reason}`);
    socketEvents.emit('connected', false);

    // If the disconnection wasn't initiated by us and we aren't already reconnecting
    if (reason !== 'io client disconnect' && !reconnecting) {
      reconnecting = true;
    }
  });

  socket.on('connect_error', (error) => {
    console.error('Socket.IO connection error:', error);
    socketEvents.emit('connected', false);
  });

  // Set up custom event handler for all events
  socket.onAny((event, ...args) => {
    // Re-emit the event to our event bus
    socketEvents.emit(event, args[0]);
  });

  // Set up the default error handler
  socket.on('error', (error) => {
    console.error('Socket.IO error:', error);
  });

  isInitialized = true;
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
    socket.disconnect();
    socket = null;
  }

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
 * Send a ping to keep the connection alive
 */
export function sendPing(): void {
  sendMessage('ping');
}