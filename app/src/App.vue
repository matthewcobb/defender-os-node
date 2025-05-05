<template>
  <div class="app">
    <!-- Wedding Component -->
    <WeddingComponent v-if="showWeddingMode" @close="closeWeddingMode" />

    <!-- Regular App Content -->
    <template v-else>
      <DefenderOS />
      <div class="carplay-container" ref="carplayContainer">
        <CarPlayDisplay v-if="width > 0" :width="width" :height="height" />
      </div>
    </template>

    <ToastMessage
      :show="toastState.show"
      :text="toastState.text"
      :type="toastState.type"
      :duration="toastState.duration"
      @update:show="updateToastVisibility"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import CarPlayDisplay from './components/CarPlayDisplay.vue';
import DefenderOS from './components/DefenderOS.vue';
import ToastMessage from './components/ToastMessage.vue';
import WeddingComponent from './components/WeddingComponent.vue';
import { apiService } from './features/system/services/api';
import { useToast } from './features';
import { useGpioStore } from './stores/gpioStore';
import { useWifi } from './features';

const router = useRouter();
const carplayContainer = ref<HTMLDivElement | null>(null);
const width = ref(0);
const height = ref(0);
const showWeddingMode = ref(false);

// Use the global toast system
const { state: toastState, hideToast } = useToast();
const updateToastVisibility = (show: boolean) => {
  if (!show) hideToast();
};

// Initialize the WiFi service (websocket connection is now handled automatically in useWifi)
useWifi();

// Function to close wedding mode
const closeWeddingMode = () => {
  showWeddingMode.value = false;
};

// Initialize the GPIO store
const gpioStore = useGpioStore();
gpioStore.init(router);

onMounted(async () => {
  // Check if wedding mode is enabled
  const weddingModeEnabled = localStorage.getItem('weddingMode') === 'true';
  if (weddingModeEnabled) {
    showWeddingMode.value = true;
  }

  // Wait for next DOM update so container is rendered
  await nextTick();

  // Get dimensions after container is rendered
  width.value = carplayContainer.value?.clientWidth || window.innerWidth;
  height.value = carplayContainer.value?.clientHeight || window.innerHeight;

  console.log('Container dimensions:', width.value, height.value);

  // Remove the splash screen once the app is fully loaded
  try {
    const result = await apiService.removeSplashScreen();
    if (result.status === 'success') {
      const { success } = useToast();
      success('App ready');
    } else if (result.status === 'warning') {
      console.log('Splash screen was already closed');
    } else {
      console.error('Failed to remove splash screen:', result.message);
    }
  } catch (error) {
    console.error('Failed to remove splash screen:', error);
  }
});

onUnmounted(() => {
  // Clean up GPIO store when app is unmounted
  gpioStore.cleanup();
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