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
import { socketEvents, initSocketIO } from '../features/system/services/socketio';
import { computed, onMounted, ref, onUnmounted } from 'vue';

defineProps<{
  isActive: boolean;
}>();

defineEmits<{
  menuToggle: [menuName: string];
}>();

// Initialize socket connection
initSocketIO();

// Track wifi status
const wifiStatus = ref<any>(null);

// Get WiFi service
const wifiService = useWifi();

// Get connection status
const isConnected = computed(() => {
  // If we have direct data from socketio, use it
  if (wifiStatus.value) {
    return wifiStatus.value.connected;
  }

  // Fall back to the useWifi hook's isConnected property
  return wifiService.isConnected.value;
});

// Set up socket event listeners
onMounted(() => {
  // Listen for wifi status updates
  socketEvents.on('wifi:status_update', (data) => {
    wifiStatus.value = data;
  });
});

// Clean up event listeners when component is unmounted
onUnmounted(() => {
  socketEvents.off('wifi:status_update');
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