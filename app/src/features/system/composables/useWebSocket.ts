import { ref, computed, readonly, onUnmounted } from 'vue';
import {
  socketEvents,
  initSocketIO,
  sendMessage,
  disconnect as disconnectSocket,
  isConnected as isSocketConnected
} from '../services/socketio';

/**
 * Vue composable for WebSocket (Socket.IO) functionality
 * Provides a reactive interface to the Socket.IO service
 */
export function useWebSocket() {
  // Initialize the socket connection
  initSocketIO();

  // Track connection state
  const connected = ref(isSocketConnected());

  // Last error message
  const lastError = ref<string | null>(null);

  // Set up connection status listener
  const setupListeners = () => {
    socketEvents.on('connected', (status) => {
      connected.value = status;
    });

    socketEvents.on('error', (error) => {
      lastError.value = typeof error === 'string' ? error : 'WebSocket error occurred';
    });
  };

  // Set up listeners initially
  setupListeners();

  // Subscribe to a Socket.IO event
  const subscribe = <T = any>(
    event: string,
    callback: (data: T) => void
  ) => {
    socketEvents.on(event, callback as any);

    // Return unsubscribe function
    return () => {
      socketEvents.off(event, callback as any);
    };
  };

  // Send a message through the socket
  const send = (event: string, data?: any): boolean => {
    return sendMessage(event, data);
  };

  // Disconnect the socket
  const disconnect = () => {
    disconnectSocket();
  };

  // Clean up event listeners when component is unmounted
  onUnmounted(() => {
    // We don't disconnect the socket on unmount
    // This allows the socket to persist between component instances
  });

  return {
    // State
    connected: readonly(connected),
    lastError: readonly(lastError),
    isConnected: computed(() => connected.value),

    // Methods
    subscribe,
    send,
    disconnect,

    // Direct access to the underlying Socket.IO functionality
    socketEvents,
    initSocketIO
  };
}