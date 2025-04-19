<template>
  <div class="top-bar small">
    <p class="app-name">
      DEFENDER<span class="fgColor-muted">OS</span>
    </p>
    <p class="font-monospace">{{ error ? '--' : temp }}ºC</p>
    <p class="font-monospace">{{ formattedTime }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useCpuTemp, createPeriodicFetcher } from '../features';

// Get CPU temperature using our composable
const { temp, error, fetchCpuTemp } = useCpuTemp();

// Set up periodic fetching for CPU temperature
const startCpuTempFetching = createPeriodicFetcher(fetchCpuTemp);

// Clock functionality
const date = ref(new Date());
const formattedTime = computed(() => {
  return date.value.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
});

// Set up all data fetching intervals
let cleanup = {
  cpuTemp: () => {},
  clock: () => {}
};

onMounted(() => {
  // Start CPU temperature updates
  cleanup.cpuTemp = startCpuTempFetching();

  // Start clock updates
  const clockInterval = setInterval(() => {
    date.value = new Date();
  }, 1000);

  cleanup.clock = () => clearInterval(clockInterval);
});

// Clean up intervals on component unmount
onUnmounted(() => {
  cleanup.cpuTemp();
  cleanup.clock();
});
</script>

<style lang="scss" scoped>
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--top-bar-bg);
  padding: 0 1rem;
  height: var(--top-bar-height);

  .app-name {
    font-weight: 600;
    margin: 0;
  }

  .cpu-temp {
    margin: 0;
  }

}
</style>