<template>
  <FullScreenDisplay
    ref="container"
    :startFullscreen="startFullscreen"
    @close="onClose"
  >
    <div class="reverse-camera-content">
      <video
        ref="videoElement"
        class="camera-feed"
        autoplay
        playsinline
        muted
      ></video>
    </div>
  </FullScreenDisplay>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, defineEmits, nextTick } from 'vue';
import FullScreenDisplay from './FullScreenDisplay.vue';

const emit = defineEmits(['close']);

const props = defineProps<{
  deviceId?: string; // Optional webcam device ID
  startFullscreen?: boolean; // Whether to start in fullscreen mode
}>();

const container = ref<HTMLDivElement | null>(null);
const videoElement = ref<HTMLVideoElement | null>(null);
const stream = ref<MediaStream | null>(null);
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

// Close the camera view
const onClose = () => {
  // Stop the camera stream
  stopCameraStream();

  // Emit close event
  emit('close');
};

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
.reverse-camera-content {
  background-color: #000;
  width: 100%;
  height: 100%;
  padding: 0 !important;
}

.camera-feed {
  width: 100%;
  height: 100%;
  object-fit: cover;
  vertical-align: middle;
}
</style>