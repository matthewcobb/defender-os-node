<template>
  <div>
    <div v-if="isConnected">
      <p><strong>Connected to:</strong> {{ currentNetwork }}</p>
      <p><strong>Signal:</strong> {{ signalStrength }}</p>
      <button @click.stop="disconnect" class="btn btn-sm btn-danger">Disconnect</button>
    </div>
    <div v-else class="wifi-status-content">
      <p>Not connected...</p>
      <button @click.stop="goToSettings" class="btn btn-sm btn-primary">Go to Settings</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useWifi } from '../../features';
import { useMenuItems } from '../../features/ui';

const router = useRouter();
const { isConnected, currentNetwork, signalStrength, disconnectNetwork } = useWifi();
const { closeMenuItem } = useMenuItems();

// Disconnect from the current WiFi network
const disconnect = async () => {
  try {
    await disconnectNetwork();
    closeMenuItem();
  } catch (error) {
    console.error('Failed to disconnect:', error);
  }
};

// Navigate to the settings page
const goToSettings = () => {
  router.push('/settings');
  closeMenuItem();
};
</script>

<style lang="scss" scoped>
button {
  margin-top: 10px;
}
</style>