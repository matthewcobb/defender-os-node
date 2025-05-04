import { ref, onMounted, onUnmounted } from 'vue';
import { io, Socket } from 'socket.io-client';

const API_URL = 'http://0.0.0.0:5000';

/**
 * Composable to manage WebSocket connections and data
 */
export function useWebSocket(eventName: string) {
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
      socket.value = io(API_URL, {
        reconnectionDelayMax: 10000,
        transports: ['websocket'],
      });

      // Handle connection event
      socket.value.on('connect', () => {
        isConnected.value = true;
        console.log(`WebSocket connected: ${eventName}`);
      });

      // Handle disconnect event
      socket.value.on('disconnect', () => {
        isConnected.value = false;
        console.log(`WebSocket disconnected: ${eventName}`);
      });

      // Handle the specific event we're interested in
      socket.value.on(eventName, (data) => {
        socketData.value = data;
      });

      // Handle connection error
      socket.value.on('connect_error', (err) => {
        error.value = `Connection error: ${err.message}`;
        console.error(`WebSocket connection error: ${err.message}`);
      });
    } catch (err: any) {
      error.value = err.message || 'Failed to connect to WebSocket';
      console.error(`WebSocket setup error: ${err}`);
    }
  };

  /**
   * Disconnect from the WebSocket server
   */
  const disconnect = () => {
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