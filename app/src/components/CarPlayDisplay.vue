<template>
  <div ref="container" class="carplay-display">
    <LoadingVideo :device-found="deviceFound ?? false" v-if="isLoading">
      <template #overlay>
        <button v-if="deviceFound === false" @click="() => checkDevice(true)" class="device-check-btn">
          Plug-In Carplay Dongle and Press
        </button>
        <div v-if="deviceFound === true" class="loading-spinner">
          <div class="spinner"></div>
        </div>
      </template>
    </LoadingVideo>

    <div
      id="videoContainer"
      :style="!isPlugged ? { display: 'none' } : {}"
      @pointerdown="sendTouchEvent"
      @pointermove="sendTouchEvent"
      @pointerup="sendTouchEvent"
      @pointercancel="sendTouchEvent"
      @pointerout="sendTouchEvent"
    >
      <canvas
        ref="canvasElement"
        id="video"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useCarplay } from '../features/carplay/composables/useCarplay';
import LoadingVideo from './LoadingVideo.vue';

const props = defineProps<{
  width: number;
  height: number;
}>();

const { isPlugged, deviceFound, isLoading, checkDevice, sendTouchEvent, setCanvas } = useCarplay(
  props.width,
  props.height
);

const canvasElement = ref<HTMLCanvasElement | null>(null);

onMounted(() => {
  if (canvasElement.value) {
    setCanvas(canvasElement.value);
  }
});
</script>

<style lang="scss" scoped>
.carplay-display {
  touch-action: none;
  width: 100%;
  height: 100%;
  border-radius: 1rem;
  overflow: hidden;
}

.device-check-btn {
  position: relative;
  z-index: 2;
  padding: 12px 20px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  cursor: pointer;
}

.loading-spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  z-index: 2;
}

.spinner {
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top: 4px solid var(--primary);
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

#videoContainer {
  width: 100%;
  height: 100%;
  margin: 0;
  padding:0;
  canvas {
    vertical-align: middle;
  }
}
</style>