<template>
  <div class="panel">
    <h2>Camera</h2>

    <div>
      <h4>Reverse Camera</h4>
      <select v-model="selectedCamera" class="select-input">
        <option value="">Default Camera</option>
        <option v-for="camera in availableCameras" :key="camera.deviceId" :value="camera.deviceId">
          {{ camera.label || `Camera ${camera.deviceId.substring(0, 8)}...` }}
        </option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';

const availableCameras = ref<MediaDeviceInfo[]>([]);
const selectedCamera = ref('');

// Function to enumerate cameras
const enumerateCameras = async () => {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    availableCameras.value = devices.filter(device => device.kind === 'videoinput');

    // Load saved camera selection from localStorage
    const savedCameraId = localStorage.getItem('reverseCameraId');
    if (savedCameraId) {
      selectedCamera.value = savedCameraId;
    }
  } catch (error) {
    console.error('Error enumerating cameras:', error);
  }
};

// Watch for camera selection changes
watch(selectedCamera, (newValue) => {
  localStorage.setItem('reverseCameraId', newValue);
});

// Initialize camera settings
onMounted(async () => {
  await enumerateCameras();
});
</script>

<style lang="scss" scoped>
.select-input {
  width: 100%;
  padding: 0.5rem;
  background-color: rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: inherit;
  font-size: 0.9rem;
}
</style>