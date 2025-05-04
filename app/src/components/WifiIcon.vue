<template>
  <div @click.stop="$emit('menuToggle', 'wifi-status')" class="wifi-container" :class="{ 'active': isActive }">
    <div class="wifi-icon" :class="{ 'connected': isConnected }">
      <Wifi v-if="isConnected" class="icon" :size="20" />
      <WifiOff v-else class="icon" :size="20" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useWifi } from '../features';
import { Wifi, WifiOff } from 'lucide-vue-next';

const props = defineProps<{
  isActive: boolean;
}>();

const emit = defineEmits<{
  menuToggle: [menuName: string];
}>();

const { isConnected } = useWifi();
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