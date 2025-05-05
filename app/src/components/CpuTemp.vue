<template>
  <p class="font-monospace">{{ error ? '--' : temp }}ºC</p>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useCpuTemp, createPeriodicFetcher } from '../features';

// Get CPU temperature using our composable
const { temp, error, fetchCpuTemp } = useCpuTemp();

// Set up periodic fetching for CPU temperature
const startCpuTempFetching = createPeriodicFetcher(fetchCpuTemp);

// Set up data fetching interval
let cleanup = () => {};

onMounted(() => {
  // Start CPU temperature updates
  cleanup = startCpuTempFetching();
});

// Clean up interval on component unmount
onUnmounted(() => {
  cleanup();
});
</script>

<style lang="scss" scoped>
.cpu-temp-container {
  position: relative;
  padding: 0.25rem;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background-color 0.2s ease;

  &.active {
    background-color: var(--panel-bg);
  }
}
</style>