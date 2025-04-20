<template>
  <div class="loading-container">
    <video
      ref="loadingVideoElement"
      class="loading-video"
      :poster="previewImage"
      :src="loadingVideo"
      muted
      playsinline
      autoplay
    ></video>
    <slot name="overlay"></slot>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';

// Import assets
import loadingVideoSrc from '../assets/loading-video.mp4';
import previewImageSrc from '../assets/preview.png';

const props = defineProps<{
  deviceFound: boolean;
  loopEndTime?: number; // Time in seconds where the loop should end before deviceFound is true
}>();

const loadingVideoElement = ref<HTMLVideoElement | null>(null);
let videoLoopInterval: number | null = null;

// Define asset paths
const loadingVideo = loadingVideoSrc;
const previewImage = previewImageSrc;

const setupVideoLoop = () => {
  if (!loadingVideoElement.value) return;

  const loopEndTime = props.loopEndTime || 4;

  videoLoopInterval = window.setInterval(() => {
    if (!loadingVideoElement.value) return;
    if (!props.deviceFound) {
      // Loop video between 0-3 seconds while device not found
      if (loadingVideoElement.value.currentTime >= loopEndTime) {
        loadingVideoElement.value.currentTime = 0;
      }
    } else {
      // When device is found, clear interval and let video play to the end
      if (videoLoopInterval !== null) {
        clearInterval(videoLoopInterval);
        videoLoopInterval = null;
      }
    }
  }, 100);
};

watch(() => props.deviceFound, (newValue) => {
  if (newValue && videoLoopInterval !== null) {
    clearInterval(videoLoopInterval);
    videoLoopInterval = null;
  }
});

onMounted(() => {
  if (loadingVideoElement.value) {
    // Force play the video with a user interaction simulation
    loadingVideoElement.value.muted = true; // Must be muted for autoplay
    const playPromise = loadingVideoElement.value.play();

    if (playPromise !== undefined) {
      playPromise.catch(error => {
        // Auto-play was prevented
        console.warn("Autoplay prevented:", error);
        // We'll set up the loop anyway so it's ready when play() is called
        setupVideoLoop();
      }).then(() => {
        // Autoplay started
        setupVideoLoop();
      });
    } else {
      // Older browsers might not return a promise
      setupVideoLoop();
    }
  }
});
</script>

<style lang="scss" scoped>
.loading-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;

  .loading-video {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    z-index: 1;
  }
}
</style>