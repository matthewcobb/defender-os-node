<template>
  <div class="wifi-status-dropdown">
    <!-- WiFi Status & Controls -->
    <div>
      <!-- Connected state -->
      <div v-if="isConnected" class="wifi-connected">
        <div class="status-indicator connected"></div>
        <div class="network-info">
          <p class="network-name">{{ currentNetwork }}</p>
          <p class="network-details">Signal: {{ signalStrength }}</p>
        </div>
        <button
          @click.stop="disconnect"
          class="btn btn-sm btn-danger"
          :disabled="connecting"
        >
          {{ connecting ? 'Disconnecting...' : 'Disconnect' }}
        </button>
      </div>

      <!-- Not connected state -->
      <div v-else class="wifi-disconnected">
        <div class="status-indicator disconnected"></div>
        <small>Not connected</small>
      </div>

      <!-- Favorite networks section -->
      <div v-if="favoriteNetworks.length > 0" class="favorites-section">
        <h4>Favorite Networks</h4>
        <div class="favorites-list">
          <div
            v-for="(favorite, index) in favoriteNetworks"
            :key="index"
            class="favorite-item"
          >
            <div class="favorite-info">
              <small class="favorite-name">{{ favorite.ssid }}</small>
              <p class="favorite-details">
                {{ favorite.auto_connect ? 'Auto-connect enabled' : '' }}
              </p>
            </div>
            <button
              class="btn btn-sm btn-primary"
              @click="connectToFavoriteNetwork(favorite.ssid)"
              :disabled="connecting || (isConnected && currentNetwork === favorite.ssid)"
            >
              {{
                connecting ? 'Connecting...' :
                (isConnected && currentNetwork === favorite.ssid ? 'Connected' : 'Connect')
              }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Network Scanning Section -->
    <div class="scan-section">
      <button class="btn btn-primary btn-sm" @click="scanForNetworks" :disabled="scanning">
        {{ scanning ? 'Scanning...' : 'Scan for Networks' }}
      </button>
      <div v-if="networks.length > 0" class="networks-list">
        <div
          v-for="(network, index) in networks"
          :key="index"
          class="network-item"
        >
          <div class="network-info">
            <p class="network-name">{{ network.ssid }}</p>
            <p class="network-details">Signal: {{ network.signal }}</p>
          </div>

          <div class="network-actions">
            <span v-if="network.is_favorite" class="favorite-badge">Favorite</span>
            <button
              class="btn btn-sm btn-primary"
              @click="showConnectForm(network.ssid)"
              :disabled="connecting || (isConnected && currentNetwork === network.ssid)"
            >
              {{
                connecting && selectedNetwork === network.ssid ? 'Connecting...' :
                (isConnected && currentNetwork === network.ssid ? 'Connected' : 'Connect')
              }}
            </button>
          </div>
        </div>
      </div>

      <!-- Connection Form -->
      <div v-if="showingConnectForm" class="connect-form">
        <h4>Connect to {{ selectedNetwork }}</h4>
        <div class="form-group">
          <label for="password">Password:</label>
          <input
            type="password"
            id="password"
            v-model="password"
            class="form-control"
            @keyup.enter="connectToSelectedNetwork"
          />
        </div>
        <div class="form-actions">
          <button
            @click="hideConnectForm"
            class="btn btn-sm btn-secondary"
          >
            Cancel
          </button>
          <button
            @click="connectToSelectedNetwork"
            class="btn btn-sm btn-primary"
            :disabled="connecting"
          >
            {{ connecting ? 'Connecting...' : 'Connect' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useMenuItems } from '../../features/ui';
import { useWifi } from '../../features';
import { useToast } from '../../features';

const { closeMenuItem } = useMenuItems();
const {
  networks,
  scanning,
  connecting,
  selectedNetwork,
  password,
  isConnected,
  currentNetwork,
  signalStrength,
  favoriteNetworks,
  scanNetworks,
  connectToNetwork,
  disconnectNetwork,
  connectToFavorite
} = useWifi();

const { success, error } = useToast();
const showingConnectForm = ref(false);

// Scan for available networks
const scanForNetworks = async () => {
  try {
    await scanNetworks();
  } catch (err: any) {
    error(`Failed to scan: ${err.message}`);
  }
};

// Connect to a favorite network
const connectToFavoriteNetwork = async (ssid: string) => {
  if (connecting.value) return;

  try {
    await connectToFavorite(ssid);
    success(`Connected to ${ssid}`);
    setTimeout(() => closeMenuItem(), 1000); // Close after a delay to see the status update
  } catch (err: any) {
    error(`Failed to connect: ${err.message}`);
  }
};

// Disconnect from current WiFi network
const disconnect = async () => {
  if (connecting.value) return;

  try {
    await disconnectNetwork();
    success('Disconnected from WiFi');
    setTimeout(() => closeMenuItem(), 1000); // Close after a delay to see the status update
  } catch (err: any) {
    error(`Failed to disconnect: ${err.message}`);
  }
};

// Show connection form for a network
const showConnectForm = (ssid: string) => {
  // If already connected to this network, do nothing
  if (isConnected.value && currentNetwork.value === ssid) {
    return;
  }

  selectedNetwork.value = ssid;
  password.value = ''; // Reset password field
  showingConnectForm.value = true;
};

// Hide connection form
const hideConnectForm = () => {
  showingConnectForm.value = false;
};

// Connect to the selected network
const connectToSelectedNetwork = async () => {
  if (connecting.value || !selectedNetwork.value) return;

  try {
    await connectToNetwork(selectedNetwork.value, password.value);
    success(`Connected to ${selectedNetwork.value}`);
    showingConnectForm.value = false;
    setTimeout(() => closeMenuItem(), 1000); // Close after a delay to see the status update
  } catch (err: any) {
    error(`Failed to connect: ${err.message}`);
  }
};
</script>

<style lang="scss" scoped>
.wifi-status-dropdown {
  min-width: 300px;
  padding: 0.75rem;
}

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

.network-info {
  flex-grow: 1;
  padding: 0 0.5rem;
}

.network-name {
  font-weight: bold;
  margin: 0;
  font-size: 0.9rem;
}

.network-details {
  font-size: 0.8rem;
  color: var(--fgColor-muted);
  margin: 0;
}

.favorites-section {
  margin-top: 1rem;
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.favorite-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.1);
}

.favorite-info {
  flex-grow: 1;

  .favorite-name {
    font-weight: bold;
    margin: 0;
  }

  .favorite-details {
    font-size: 0.8rem;
    color: var(--fgColor-muted);
    margin: 0;
  }
}

.scan-section {
  margin-top: 1rem;
}

.networks-list {
  max-height: 200px;
  overflow-y: auto;
  margin-top: 0.75rem;
}

.network-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.1);
  margin-bottom: 0.5rem;

  &:last-child {
    margin-bottom: 0;
  }
}

.network-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.favorite-badge {
  background-color: var(--primary);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.connect-form {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 4px;

  h4 {
    margin-top: 0;
    margin-bottom: 0.75rem;
    font-size: 1rem;
  }

  .form-group {
    margin-bottom: 0.75rem;

    label {
      display: block;
      margin-bottom: 0.25rem;
      font-size: 0.9rem;
    }

    input {
      width: 100%;
      padding: 0.4rem;
      border-radius: 4px;
      border: 1px solid rgba(0, 0, 0, 0.2);
      background-color: var(--panel-bg);
      color: var(--fgColor);
    }
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
  }
}

button {
  margin-left: 0.5rem;
}
</style>