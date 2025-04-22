<template>
  <div class="reverse-view">
    <ReverseCameraDisplay
      v-if="showCamera"
      :deviceId="cameraDeviceId"
      :startFullscreen="startFullscreen"
      @close="closeCamera"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import ReverseCameraDisplay from '../components/ReverseCameraDisplay.vue';
import { isReversing } from '../features/system/services/gpio'; // Use the main GPIO service export

const router = useRouter();
const route = useRoute();
const showCamera = ref(true);
const cameraDeviceId = ref<string | undefined>(undefined);
const isFromReverseSensor = ref(false);
const startFullscreen = ref(false);
const closeTimer = ref<number | null>(null);

// Function to close the camera and navigate back
const closeCamera = () => {
  showCamera.value = false;

  router.back();
};

// Get the configured camera device ID from settings (if available)
const loadCameraSettings = async () => {
  try {
    // Load camera device ID from localStorage
    const savedCameraId = localStorage.getItem('reverseCameraId');
    if (savedCameraId) {
      cameraDeviceId.value = savedCameraId;
    }
  } catch (error) {
    console.error('Error loading camera settings:', error);
  }
};

// Clear any existing close timer
const clearCloseTimer = () => {
  if (closeTimer.value !== null) {
    window.clearTimeout(closeTimer.value);
    closeTimer.value = null;
  }
};

// Watch the isReversing state from the shared GPIO service
watch(isReversing, (newValue) => {
  console.log('isReversing', newValue);
  // If this is a reverse state event, mark this as coming from the sensor
  if (newValue === true) {
    isFromReverseSensor.value = true;

    // Clear any pending close timer
    clearCloseTimer();
  }
  // If we're no longer reversing and we came from the reverse sensor
  else if (newValue === false && isFromReverseSensor.value) {
    // Set a timer to close the view after 5 seconds
    clearCloseTimer(); // Clear any existing timer first

    closeTimer.value = window.setTimeout(() => {
      closeCamera();
      closeTimer.value = null;
    }, 5000); // 5 seconds delay

    console.log('Reverse state off: Camera will close in 5 seconds unless reversed again');
  }
});

onMounted(async () => {
  await loadCameraSettings();

  // Check if this view was opened via the sensor (from URL params)
  isFromReverseSensor.value = route.query.sensor === 'true';

  // Set fullscreen based on query parameter
  startFullscreen.value = route.query.fullscreen === 'true';

  // Also check current reverse state in case we missed an update
  if (isReversing.value) {
    isFromReverseSensor.value = true;
  }
});

onUnmounted(() => {
  // Clean up any pending timers
  clearCloseTimer();
});
</script>

<style lang="scss" scoped>
.reverse-view {
  width: 100%;
  height: 100%;
  background-color: #000;
  border-radius: 0.5rem;
}
</style>