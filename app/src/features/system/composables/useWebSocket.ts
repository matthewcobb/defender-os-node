import { ref, onMounted, onUnmounted } from 'vue';
import { io, Socket } from 'socket.io-client';

// Get API URL from window location for better compatibility
const getApiUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
  const host = window.location.hostname || '0.0.0.0';  // Use hostname if available
  const port = '5000';

  return `${protocol}://${host}:${port}`;
};

const API_URL = getApiUrl();

// Track persistent socket connections
interface PersistentSocketData {
  socket: Socket;
  socketData: any;
  isConnected: boolean;
  error: string;
  refCount: number;
}

const persistentSockets = new Map<string, PersistentSocketData>();

/**
 * Composable to manage WebSocket connections and data
 * @param eventName The event to listen for
 * @param persistent Whether to keep the connection alive between component instances
 */
export function useWebSocket(eventName: string, persistent: boolean = false) {
  // Use persistent socket if requested and available
  if (persistent && persistentSockets.has(eventName)) {
    const socketData = persistentSockets.get(eventName)!;
    socketData.refCount++;

    return {
      socketData: ref(socketData.socketData),
      isConnected: ref(socketData.isConnected),
      error: ref(socketData.error),
      connect: () => {}, // No-op as connection is already managed
      disconnect: () => {} // No-op as disconnection is managed by the persistent socket
    };
  }

  const socketData = ref<any>(null);
  const socket = ref<Socket | null>(null);
  const isConnected = ref(false);
  const error = ref<string>('');

  /**
   * Connect to the WebSocket server
   */
  const connect = () => {
    if (socket.value && isConnected.value) return;

    try {
      // Create the socket connection
      const socketInstance = io(API_URL, {
        reconnectionDelayMax: 10000,
        reconnection: true,
        reconnectionAttempts: Infinity,
        reconnectionDelay: 1000,
        timeout: 20000,
        transports: ['websocket', 'polling'],
      });

      socket.value = socketInstance;

      // Handle connection event
      socket.value.on('connect', () => {
        isConnected.value = true;
        error.value = '';
        console.log(`WebSocket connected: ${eventName}`);
      });

      // Handle disconnect event
      socket.value.on('disconnect', () => {
        isConnected.value = false;
        console.log(`WebSocket disconnected: ${eventName}`);
      });

      // Handle the specific event we're interested in
      socket.value.on(eventName, (data) => {
        console.log(`WebSocket event received: ${eventName}`, data);
        socketData.value = data;

        // Update persistent data if this is a persistent socket
        if (persistent && persistentSockets.has(eventName)) {
          persistentSockets.get(eventName)!.socketData = data;
        }
      });

      // Handle connection error
      socket.value.on('connect_error', (err) => {
        error.value = `Connection error: ${err.message}`;
        console.error(`WebSocket connection error: ${err.message}`);
      });

      // If persistent, store in the map
      if (persistent) {
        persistentSockets.set(eventName, {
          socket: socketInstance,
          socketData: socketData.value,
          isConnected: isConnected.value,
          error: error.value,
          refCount: 1
        });
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to connect to WebSocket';
      console.error(`WebSocket setup error: ${err}`);
    }
  };

  /**
   * Disconnect from the WebSocket server
   */
  const disconnect = () => {
    // For persistent sockets, don't disconnect
    if (persistent && persistentSockets.has(eventName)) {
      const socketData = persistentSockets.get(eventName)!;
      socketData.refCount--;

      // Only disconnect if no more components are using this socket
      if (socketData.refCount <= 0) {
        socketData.socket.disconnect();
        persistentSockets.delete(eventName);
      }
      return;
    }

    // Regular (non-persistent) socket disconnect
    if (socket.value) {
      socket.value.disconnect();
      socket.value = null;
      isConnected.value = false;
    }
  };

  // Connect when component is mounted
  onMounted(() => {
    connect();
  });

  // Disconnect when component is unmounted
  onUnmounted(() => {
    disconnect();
  });

  return {
    socketData,
    isConnected,
    error,
    connect,
    disconnect
  };
}