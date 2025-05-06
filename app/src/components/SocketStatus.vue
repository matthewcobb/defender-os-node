<template>
  <div
    class="socket-status"
    :class="{ 'connected': isConnected, 'active': isActive }"
    :title="isConnected ? 'Socket.IO Connected' : 'Socket.IO Disconnected'"
    @click.stop="$emit('menuToggle', 'socket-status')"
  >
    <div class="status-indicator"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { socketEvents } from '../features/system/services/socketio';

const isConnected = ref(false);

defineProps<{
  isActive?: boolean;
}>();

defineEmits<{
  menuToggle: [menuName: string];
}>();

// Handle connection status changes
const handleConnectionChange = (connected: boolean) => {
  isConnected.value = connected;
};

onMounted(() => {
  // Listen for socket connection events
  socketEvents.on('connected', handleConnectionChange);
});

onUnmounted(() => {
  // Clean up event listeners
  socketEvents.off('connected', handleConnectionChange);
});
</script>

<style lang="scss" scoped>
.socket-status {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.35rem 0.5rem;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background-color: var(--panel-bg);
  }

  &.active {
    background-color: var(--panel-bg);
  }

  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--fgColor-muted);
    transition: all 0.3s ease;
    position: relative;
  }

  &.connected .status-indicator {
    background-color: var(--primary);
    box-shadow: 0 0 4px var(--primary);

    &:after {
      content: '';
      position: absolute;
      top: -2px;
      left: -2px;
      right: -2px;
      bottom: -2px;
      border-radius: 50%;
      background-color: transparent;
      border: 1px solid var(--primary);
      opacity: 0.5;
      animation: pulse 2s infinite;
    }
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 0.5;
  }
  70% {
    transform: scale(1.5);
    opacity: 0;
  }
  100% {
    transform: scale(1);
    opacity: 0;
  }
}
</style>