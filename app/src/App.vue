<template>
  <div class="app">
    <DefenderOS />
    <div class="carplay-container" ref="carplayContainer">
      <CarPlayDisplay v-if="width > 0" :width="width" :height="height" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import CarPlayDisplay from './components/CarPlayDisplay.vue';
import DefenderOS from './components/DefenderOS.vue';
import { apiService } from './features/system/services/api';

const carplayContainer = ref<HTMLDivElement | null>(null);
const width = ref(0);
const height = ref(0);

onMounted(async () => {
  // Wait for next DOM update so container is rendered
  await nextTick();

  // Get dimensions after container is rendered
  width.value = carplayContainer.value?.clientWidth || window.innerWidth;
  height.value = carplayContainer.value?.clientHeight || window.innerHeight;

  console.log('Container dimensions:', width.value, height.value);

  // Remove the splash screen once the app is fully loaded
  try {
    await apiService.removeSplashScreen();
    console.log('Splash screen removed');
  } catch (error) {
    console.error('Failed to remove splash screen:', error);
  }
});
</script>

<style scoped>
.app {
  height: 100%;
  width: 100%;
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 1rem;
}
</style>