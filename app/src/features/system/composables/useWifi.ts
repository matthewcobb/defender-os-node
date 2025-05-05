import { ref, computed, readonly, onUnmounted } from 'vue';
import { apiService } from '../services/api';
import { socketEvents, initSocketIO, isConnected as isSocketConnected } from '../services/socketio';

// Define types for WiFi data
export interface WifiStatus {
  connected: boolean;
  ssid: string | null;
  signal_strength: string | null;
  favorites: WifiFavorite[];
  error?: string;
}

export interface WifiFavorite {
  ssid: string;
  password: string;
  auto_connect: boolean;
}

export interface WifiNetwork {
  ssid: string;
  signal: string;
  is_favorite: boolean;
}

// Create singleton state that persists between component instances
const state = {
  error: ref<string>(''),
  connecting: ref<boolean>(false),
  scanning: ref<boolean>(false),
  networks: ref<WifiNetwork[]>([]),
  selectedNetwork: ref<string>(''),
  password: ref<string>(''),
  wifiStatus: ref<WifiStatus | null>(null)
};

// Initialize socket connection outside the composable to ensure single instance
initSocketIO();

// Setup socket event listener once to avoid multiple handlers
socketEvents.on('wifi:status_update', (data: WifiStatus) => {
  state.wifiStatus.value = data;
  console.log('WiFi status updated via Socket.IO:', data);
});

/**
 * Composable to manage WiFi connections
 */
export function useWifi() {
  // Computed properties
  const isConnected = computed(() => state.wifiStatus.value?.connected || false);
  const currentNetwork = computed(() => state.wifiStatus.value?.ssid || null);
  const signalStrength = computed(() => state.wifiStatus.value?.signal_strength || null);
  const favoriteNetworks = computed<WifiFavorite[]>(() => state.wifiStatus.value?.favorites || []);
  const socketConnected = computed(() => isSocketConnected());

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
      throw err;
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
    const favorite = favoriteNetworks.value.find(f => f.ssid === favoriteSsid);
    if (!favorite) {
      throw new Error('Favorite network not found');
    }
    return connectToNetwork(favorite.ssid, favorite.password);
  };

  // We don't need onMounted anymore as socket handling is done outside
  // But we do need to make sure multiple registrations of the event don't occur
  onUnmounted(() => {
    // Not removing the global handler to ensure state updates continue
    // We only remove specific component-level handlers if needed
  });

  return {
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
    isSocketConnected: socketConnected
  };
}