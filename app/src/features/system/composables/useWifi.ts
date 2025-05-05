import { ref, computed, onMounted, readonly } from 'vue';
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
  status: ref<WifiStatus | null>(null),
  error: ref<string>(''),
  loading: ref<boolean>(false),
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
  // Computed property to get current WiFi status from websocket
  const wifiStatus = computed(() => {
    if (persistentSocket.socketData.value) {
      return persistentSocket.socketData.value;
    }
    return state.status.value;
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
   * Fetch WiFi status from the API
   */
  const fetchWifiStatus = async () => {
    state.loading.value = true;
    state.error.value = '';

    try {
      const data = await apiService.getWifiStatus();
      state.status.value = data;
    } catch (err: any) {
      state.error.value = err.message || 'Failed to fetch WiFi status';
    } finally {
      state.loading.value = false;
    }
  };

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

  // Initialize WiFi state if not already done
  onMounted(() => {
    if (!state.initialized.value) {
      fetchWifiStatus();
      state.initialized.value = true;
    }
  });

  return {
    status: readonly(state.status),
    wifiStatus,
    error: readonly(state.error),
    loading: readonly(state.loading),
    connecting: readonly(state.connecting),
    scanning: readonly(state.scanning),
    networks: readonly(state.networks),
    isConnected,
    currentNetwork,
    signalStrength,
    favoriteNetworks,
    selectedNetwork: state.selectedNetwork,
    password: state.password,
    fetchWifiStatus,
    scanNetworks,
    connectToNetwork,
    disconnectNetwork,
    connectToFavorite
  };
}