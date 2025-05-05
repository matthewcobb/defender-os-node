<template>
  <div @click.stop="$emit('menuToggle', 'wifi-status')" class="wifi-container" :class="{ 'active': isActive }">
    <div class="wifi-icon" :class="{ 'connected': isConnected }">
      <Wifi v-if="isConnected" class="icon" :size="32" />
      <WifiOff v-else class="icon" :size="32" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useWifi } from '../features';
import { Wifi, WifiOff } from 'lucide-vue-next';
import { useWebSocket } from '../features/system/composables/useWebSocket';
import { computed, onMounted, watch } from 'vue';

defineProps<{
  isActive: boolean;
}>();

defineEmits<{
  menuToggle: [menuName: string];
}>();

// Use persistent websocket connection for wifi status updates
const { socketData, isConnected: socketConnected, connect } = useWebSocket('wifi:status_update', true);

// Get WiFi service for reconnection if needed
const wifiService = useWifi();

// Get connection status from the websocket directly
const isConnected = computed(() => {
  // If we have websocket data, use it to determine connection status
  if (socketData.value) {
    return socketData.value.connected;
  }

  // Fall back to the useWifi hook's isConnected property
  return wifiService.isConnected.value;
});

// Ensure socket is connected when component mounts
onMounted(() => {
  if (!socketConnected.value) {
    console.log('WifiIcon: WebSocket not connected, connecting...');
    connect();
  }

  // Watch for socket connection status changes
  watch(socketConnected, (connected) => {
    if (!connected) {
      console.log('WifiIcon: WebSocket disconnected, reconnecting...');
      connect();
    }
  });
});
</script>

<style lang="scss" scoped>
.wifi-container {
  position: relative;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: background-color 0.2s ease;

  &.active {
    background-color: var(--panel-bg);
  }
}

.wifi-icon {
  cursor: pointer;
  color: var(--fgColor-muted);

  &.connected {
    color: var(--success);
  }

  .icon {
    transition: color 0.3s ease;
  }
}
</style>