import { ref, computed } from 'vue';
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

/**
 * Composable to manage WiFi connections
 */
export function useWifi() {
  const status = ref<WifiStatus | null>(null);
  const error = ref<string>('');
  const loading = ref<boolean>(false);
  const connecting = ref<boolean>(false);
  const scanning = ref<boolean>(false);
  const networks = ref<any[]>([]);

  // For connection form
  const selectedNetwork = ref<string>('');
  const password = ref<string>('');

  // Setup websocket for WiFi status updates
  const { socketData } = useWebSocket('wifi:status_update');

  // Computed property to get current WiFi status from websocket
  const wifiStatus = computed(() => {
    if (socketData.value) {
      return socketData.value;
    }
    return status.value;
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
    loading.value = true;
    error.value = '';

    try {
      const data = await apiService.getWifiStatus();
      status.value = data;
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch WiFi status';
    } finally {
      loading.value = false;
    }
  };

  /**
   * Scan for available WiFi networks
   */
  const scanNetworks = async () => {
    scanning.value = true;
    error.value = '';

    try {
      const data = await apiService.scanWifiNetworks();
      networks.value = data.networks || [];
    } catch (err: any) {
      error.value = err.message || 'Failed to scan for networks';
    } finally {
      scanning.value = false;
    }
  };

  /**
   * Connect to a WiFi network
   */
  const connectToNetwork = async (ssid: string, pwd: string = '') => {
    connecting.value = true;
    error.value = '';

    try {
      const data = await apiService.connectToWifi(ssid, pwd);

      if (!data.success) {
        throw new Error(data.error || 'Failed to connect');
      }

      return data;
    } catch (err: any) {
      error.value = err.message || 'Failed to connect to network';
      throw err;
    } finally {
      connecting.value = false;
    }
  };

  /**
   * Disconnect from current network
   */
  const disconnectNetwork = async () => {
    connecting.value = true;
    error.value = '';

    try {
      const data = await apiService.disconnectWifi();

      if (!data.success) {
        throw new Error(data.error || 'Failed to disconnect');
      }

      return data;
    } catch (err: any) {
      error.value = err.message || 'Failed to disconnect from network';
      throw err;
    } finally {
      connecting.value = false;
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

  return {
    status,
    wifiStatus,
    error,
    loading,
    connecting,
    scanning,
    networks,
    isConnected,
    currentNetwork,
    signalStrength,
    favoriteNetworks,
    selectedNetwork,
    password,
    fetchWifiStatus,
    scanNetworks,
    connectToNetwork,
    disconnectNetwork,
    connectToFavorite
  };
}