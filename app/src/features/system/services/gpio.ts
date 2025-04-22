import { useRouter } from 'vue-router';
import { isReversing, isConnected } from './gpio-state';

// Re-export state for components that import from this file
export { isReversing, isConnected };

let ws: WebSocket | null = null;
let reconnectTimer: number | null = null;
let router: ReturnType<typeof useRouter> | null = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY = 30000; // 30 seconds maximum delay

/**
 * Initialize the GPIO WebSocket service
 * @param useRouterInstance The router instance to use for navigation
 */
export function initGpioService(useRouterInstance: ReturnType<typeof useRouter>) {
  router = useRouterInstance;

  // Connect immediately
  connect();

  // Reconnect when online after being offline
  window.addEventListener('online', () => {
    if (!isConnected.value) {
      // Reset reconnect attempts when we get a network recovery
      reconnectAttempts = 0;
      connect();
    }
  });

  return {
    isReversing,
    isConnected
  };
}

/**
 * Connect to the WebSocket server
 */
function connect() {
  // Clear any existing reconnect timer
  if (reconnectTimer !== null) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  // Get the host from the current URL
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.hostname;
  const port = '5000'; // Same port as your Python backend

  const wsUrl = `${wsProtocol}//${host}:${port}/gpio/events`;

  // Close any existing connection
  if (ws) {
    ws.close();
  }

  // Create new WebSocket connection
  ws = new WebSocket(wsUrl);

  // Set up ping/pong to maintain connection and detect disconnections
  let pingInterval: number | null = null;
  let pongTimeout: number | null = null;

  // Setup timeout for connection attempt
  const connectionTimeout = setTimeout(() => {
    if (ws && ws.readyState !== WebSocket.OPEN) {
      ws.close();
      onConnectionFailed();
    }
  }, 5000);

  ws.onopen = () => {
    console.log('GPIO WebSocket connected');
    isConnected.value = true;
    reconnectAttempts = 0;

    // Clear connection timeout
    clearTimeout(connectionTimeout);

    // Set up ping interval to keep connection alive
    pingInterval = window.setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        // Send ping
        ws.send(JSON.stringify({ type: 'ping' }));

        // Set timeout for pong
        if (pongTimeout) clearTimeout(pongTimeout);
        pongTimeout = window.setTimeout(() => {
          // No pong received, connection might be dead
          if (ws) ws.close();
        }, 5000);
      }
    }, 30000); // Every 30 seconds
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      // Handle pong from server
      if (data.type === 'pong') {
        if (pongTimeout) {
          clearTimeout(pongTimeout);
          pongTimeout = null;
        }
        return;
      }

      if (data.event === 'reverse_state_change' || data.event === 'initial_state') {
        const newReversingState = data.data?.is_reversing ?? false;

        // Update state
        isReversing.value = newReversingState;

        // Handle navigation based on reversing state
        if (newReversingState) {
          // If we start reversing and we have a router, navigate to the reverse camera view
          if (router && router.currentRoute.value.name !== 'reverse') {
            // Add query parameter to indicate this was triggered by sensor
            router.push({
              path: '/reverse',
              query: { sensor: 'true', fullscreen: 'true' }
            });
          }
        }
        // We don't handle navigation away from the reverse view here - that's done in ReverseView component
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('GPIO WebSocket error:', error);
    clearTimeout(connectionTimeout);
  };

  ws.onclose = () => {
    console.log('GPIO WebSocket disconnected');
    isConnected.value = false;

    // Clean up intervals and timeouts
    if (pingInterval) {
      clearInterval(pingInterval);
      pingInterval = null;
    }

    if (pongTimeout) {
      clearTimeout(pongTimeout);
      pongTimeout = null;
    }

    clearTimeout(connectionTimeout);

    // Handle reconnection
    onConnectionFailed();
  };
}

/**
 * Handle connection failures with exponential backoff
 */
function onConnectionFailed() {
  // Exponential backoff for reconnection attempts
  reconnectAttempts++;
  const delay = Math.min(1000 * Math.pow(1.5, reconnectAttempts), MAX_RECONNECT_DELAY);

  // Schedule reconnection attempt
  reconnectTimer = window.setTimeout(() => {
    connect();
  }, delay);

  console.log(`Scheduling reconnection attempt in ${delay}ms`);
}

/**
 * Disconnect the WebSocket
 */
export function disconnect() {
  if (ws) {
    ws.close();
    ws = null;
  }

  if (reconnectTimer !== null) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
}