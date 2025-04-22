<template>
  <div
    ref="container"
    class="reverse-camera-display"
    :class="{ 'fullscreen': isFullscreen }"
  >
    <video
      ref="videoElement"
      class="camera-feed"
      autoplay
      playsinline
      muted
    ></video>

    <div class="controls">
      <button class="close-btn" @click="onClose">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
          <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
      </button>
      <button class="fullscreen-btn" @click="toggleFullscreen">
        <svg v-if="!isFullscreen" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
          <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
          <path fill="currentColor" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, defineEmits, nextTick, watch } from 'vue';

const emit = defineEmits(['close']);

const props = defineProps<{
  deviceId?: string; // Optional webcam device ID
  startFullscreen?: boolean; // Whether to start in fullscreen mode
}>();

const container = ref<HTMLDivElement | null>(null);
const videoElement = ref<HTMLVideoElement | null>(null);
const stream = ref<MediaStream | null>(null);
const isFullscreen = ref(false);
const isCameraActive = ref(false);

// Stop the camera stream
const stopCameraStream = () => {
  if (stream.value) {
    const tracks = stream.value.getTracks();
    tracks.forEach(track => {
      track.stop();
    });
    stream.value = null;
  }

  if (videoElement.value) {
    videoElement.value.srcObject = null;
  }

  isCameraActive.value = false;
};

// Start the webcam stream with optimized settings
const startCamera = async () => {
  try {
    if (!videoElement.value) return;

    // Ensure any existing stream is stopped
    stopCameraStream();

    // Get optimal camera resolution based on screen size
    // For a rear-view camera, we want good resolution but not excessive
    const idealWidth = Math.min(window.innerWidth, 1280); // Cap at 720p-ish
    const idealHeight = Math.min(window.innerHeight, 720);

    // Get user media with the specified device or default camera
    // with optimized constraints for a safety-critical feature
    const constraints: MediaStreamConstraints = {
      video: {
        deviceId: props.deviceId ? { exact: props.deviceId } : undefined,
        facingMode: !props.deviceId ? { ideal: 'environment' } : undefined,
        width: { ideal: idealWidth },
        height: { ideal: idealHeight },
        frameRate: { min: 15, ideal: 30 }, // Safety features need good framerates
      },
      audio: false
    };

    stream.value = await navigator.mediaDevices.getUserMedia(constraints);

    // Check again if videoElement is still available after the async call
    if (videoElement.value) {
      videoElement.value.srcObject = stream.value;

      // Listen for loadedmetadata event to ensure video is ready
      videoElement.value.onloadedmetadata = () => {
        if (videoElement.value) {
          videoElement.value.play().catch(e => {
            console.error('Error playing video:', e);
          });
        }
        isCameraActive.value = true;
      };
    } else {
      // If component was unmounted during async operation, clean up the stream
      stopCameraStream();
    }
  } catch (error) {
    console.error('Error accessing camera:', error);
    isCameraActive.value = false;
  }
};

// Toggle fullscreen mode
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

// Close the camera view
const onClose = () => {
  // Stop the camera stream
  stopCameraStream();

  // Emit close event
  emit('close');
};

// Set initial fullscreen state based on prop
watch(() => props.startFullscreen, (newValue) => {
  if (newValue !== undefined) {
    isFullscreen.value = newValue;
  }
}, { immediate: true });

onMounted(async () => {
  // Use nextTick to ensure DOM is fully rendered before accessing the video element
  await nextTick();
  startCamera();
});

onUnmounted(() => {
  // Clean up everything on unmount
  stopCameraStream();
});
</script>

<style lang="scss" scoped>
.reverse-camera-display {
  background-color: #000;
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 0.5rem;
  overflow: hidden;

  &.fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 9999;
    border-radius: 0;
  }
}

.camera-feed {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.controls {
  position: absolute;
  top: 1rem;
  right: 1rem;
  display: flex;
  gap: 0.5rem;

  button {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background-color: rgba(0, 0, 0, 0.5);
    color: white;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;

    &:hover {
      background-color: rgba(0, 0, 0, 0.7);
    }
  }
}
</style>