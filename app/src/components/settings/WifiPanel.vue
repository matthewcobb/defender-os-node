<template>
  <div class="panel">
    <h2>WiFi</h2>
    <div class="wifi-status">
      <h4>Connection Status</h4>
      <div v-if="isConnected" class="wifi-connected">
        <div class="status-indicator connected"></div>
        <small>Connected to: {{ currentNetwork }}</small>
        <button class="btn btn-sm btn-danger" @click="disconnectWifi" :disabled="disconnecting">
          {{ disconnecting ? 'Disconnecting...' : 'Disconnect' }}
        </button>
      </div>
      <div v-else class="wifi-disconnected">
        <div class="status-indicator disconnected"></div>
        <small>Not connected</small>
      </div>
    </div>

    <div class="favorites-section">
      <h4>Favorite Networks</h4>
      <div v-if="favoriteNetworks.length === 0" class="no-favorites">
        <small>No favorite networks configured</small>
      </div>
      <div v-else class="favorites-list">
        <div v-for="(favorite, index) in favoriteNetworks" :key="index" class="favorite-item">
          <div class="favorite-info">
            <p class="favorite-name">{{ favorite.ssid }}</p>
            <p class="favorite-details">{{ favorite.auto_connect ? 'Auto-connect enabled' : '' }}</p>
          </div>
          <button
            class="btn btn-sm btn-primary"
            @click="connectToFavoriteNetwork(favorite.ssid)"
            :disabled="connecting || (isConnected && currentNetwork === favorite.ssid)">
            {{ connecting ? 'Connecting...' : (isConnected && currentNetwork === favorite.ssid ? 'Connected' : 'Connect') }}
          </button>
        </div>
      </div>
    </div>

    <div class="scan-section">
      <button class="btn btn-primary" @click="scanForNetworks" :disabled="scanning">
        {{ scanning ? 'Scanning...' : 'Scan for Networks' }}
      </button>
      <div v-if="networks.length > 0" class="networks-list">
        <div v-for="(network, index) in networks" :key="index" class="network-item">
          <div class="network-info">
            <p class="network-name">{{ network.ssid }}</p>
            <p class="network-details">Signal: {{ network.signal }}</p>
          </div>
          <div class="network-status">
            <span v-if="network.is_favorite" class="favorite-badge">Favorite</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useToast, useWifi } from '../../features';

// Use the global toast system
const { success, error } = useToast();

// WiFi management
const {
  isConnected,
  currentNetwork,
  favoriteNetworks,
  networks,
  scanning,
  connecting,
  connectToNetwork,
  disconnectNetwork,
  scanNetworks
} = useWifi();

const disconnecting = ref(false);

// Connect to a favorite network
const connectToFavoriteNetwork = async (ssid: string) => {
  if (connecting.value) return;

  try {
    await connectToNetwork(ssid);
    success(`Connected to ${ssid}`);
  } catch (err: any) {
    error(`Failed to connect: ${err.message}`);
  }
};

// Disconnect from current WiFi network
const disconnectWifi = async () => {
  if (disconnecting.value) return;

  disconnecting.value = true;
  try {
    await disconnectNetwork();
    success('Disconnected from WiFi');
  } catch (err: any) {
    error(`Failed to disconnect: ${err.message}`);
  } finally {
    disconnecting.value = false;
  }
};

// Scan for available networks
const scanForNetworks = async () => {
  try {
    await scanNetworks();
  } catch (err: any) {
    error(`Failed to scan: ${err.message}`);
  }
};
</script>

<style lang="scss" scoped>
.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;

  &.connected {
    background-color: var(--success);
  }

  &.disconnected {
    background-color: var(--danger);
  }
}

.wifi-connected,
.wifi-disconnected {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.1);
}

.wifi-connected {
  justify-content: space-between;
}

.favorite-item,
.network-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.1);
  margin-bottom: 0.5rem;

  &:last-child {
    margin-bottom: 0;
  }
}

.favorite-info,
.network-info {
  flex-grow: 1;

  .favorite-name,
  .network-name {
    font-weight: bold;
    margin: 0;
  }

  .favorite-details,
  .network-details {
    font-size: 0.85rem;
    color: var(--fgColor-muted);
    margin: 0;
  }
}

.favorite-badge {
  background-color: var(--primary);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.networks-list {
  max-height: 300px;
  overflow-y: auto;
  margin-top: 1rem;
}

.no-favorites {
  padding: 0.75rem;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  text-align: center;
  font-style: italic;
  color: var(--fgColor-muted);
}

.favorites-section,
.scan-section {
  margin-top: 1rem;
}
</style>