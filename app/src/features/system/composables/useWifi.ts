import { ref, computed, onMounted, readonly, watch } from 'vue';
import { apiService } from '../services/api';
import { useWebSocket } from './useWebSocket';

// Define types for WiFi data
interface WifiStatus {
  connected: boolean;
  ssid: string | null;
  signal_strength: string | null;
  favorites: WifiFavorite[];
  error?: string;
}

interface WifiFavorite {
  ssid: string;
  password: string;
  auto_connect: boolean;
}

// Create singleton state that persists between component instances
const state = {
  error: ref<string>(''),
  connecting: ref<boolean>(false),
  scanning: ref<boolean>(false),
  networks: ref<any[]>([]),
  selectedNetwork: ref<string>(''),
  password: ref<string>(''),
  initialized: ref<boolean>(false)
};

// Create a persistent socket connection that won't be destroyed
const persistentSocket = useWebSocket('wifi:status_update', true);

/**
 * Composable to manage WiFi connections
 */
export function useWifi() {
  // Computed property to check if the websocket is connected
  const isSocketConnected = computed(() => {
    return persistentSocket.isConnected.value;
  });

  // Computed property to get current WiFi status from websocket
  const wifiStatus = computed(() => {
    return persistentSocket.socketData.value;
  });

  // Computed property to check if there's an active connection
  const isConnected = computed(() => {
    return wifiStatus.value?.connected || false;
  });

  // Computed property to get current network name
  const currentNetwork = computed(() => {
    return wifiStatus.value?.ssid || null;
  });

  // Computed property to get signal strength
  const signalStrength = computed(() => {
    return wifiStatus.value?.signal_strength || null;
  });

  // Computed property to get favorite networks
  const favoriteNetworks = computed(() => {
    return wifiStatus.value?.favorites || [];
  });

  /**
   * Scan for available WiFi networks
   */
  const scanNetworks = async () => {
    state.scanning.value = true;
    state.error.value = '';

    try {
      const data = await apiService.scanWifiNetworks();
      state.networks.value = data.networks || [];
    } catch (err: any) {
      state.error.value = err.message || 'Failed to scan for networks';
    } finally {
      state.scanning.value = false;
    }
  };

  /**
   * Connect to a WiFi network
   */
  const connectToNetwork = async (ssid: string, pwd: string = '') => {
    state.connecting.value = true;
    state.error.value = '';

    try {
      // Make sure the websocket is connected before making API call
      if (!isSocketConnected.value) {
        persistentSocket.connect();
      }

      const data = await apiService.connectToWifi(ssid, pwd);

      if (!data.success) {
        throw new Error(data.error || 'Failed to connect');
      }

      return data;
    } catch (err: any) {
      state.error.value = err.message || 'Failed to connect to network';
      throw err;
    } finally {
      state.connecting.value = false;
    }
  };

  /**
   * Disconnect from current network
   */
  const disconnectNetwork = async () => {
    state.connecting.value = true;
    state.error.value = '';

    try {
      // Make sure the websocket is connected before making API call
      if (!isSocketConnected.value) {
        persistentSocket.connect();
      }

      const data = await apiService.disconnectWifi();

      if (!data.success) {
        throw new Error(data.error || 'Failed to disconnect');
      }

      return data;
    } catch (err: any) {
      state.error.value = err.message || 'Failed to disconnect from network';
      throw err;
    } finally {
      state.connecting.value = false;
    }
  };

  /**
   * Connect to one of the favorite networks
   */
  const connectToFavorite = async (favoriteSsid: string) => {
    // Find the favorite in the list
    const favorite = favoriteNetworks.value.find((f: WifiFavorite) => f.ssid === favoriteSsid);

    if (favorite) {
      return connectToNetwork(favorite.ssid, favorite.password);
    } else {
      throw new Error('Favorite network not found');
    }
  };

  /**
   * Reconnect the websocket if disconnected
   */
  const reconnectSocket = () => {
    if (!isSocketConnected.value) {
      console.log('Reconnecting to WebSocket for WiFi status updates...');
      persistentSocket.connect();
    }
  };

  // Initialize with websocket - no API call needed
  onMounted(() => {
    // Ensure the websocket is connected
    reconnectSocket();

    // Add debug output when socket data changes
    watch(persistentSocket.socketData, (newData) => {
      console.log('WiFi status updated via WebSocket:', newData);
    });

    // Watch socket connection status and reconnect if disconnected
    watch(isSocketConnected, (connected) => {
      if (!connected) {
        console.log('WebSocket disconnected, attempting to reconnect...');
        setTimeout(reconnectSocket, 1000);
      }
    });
  });

  return {
    wifiStatus,
    error: readonly(state.error),
    connecting: readonly(state.connecting),
    scanning: readonly(state.scanning),
    networks: readonly(state.networks),
    isConnected,
    currentNetwork,
    signalStrength,
    favoriteNetworks,
    selectedNetwork: state.selectedNetwork,
    password: state.password,
    scanNetworks,
    connectToNetwork,
    disconnectNetwork,
    connectToFavorite,
    isSocketConnected,
    reconnectSocket
  };
}