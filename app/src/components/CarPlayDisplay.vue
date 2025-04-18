<template>
  <div ref="container" class="carplay-display">
    <div class="loading-container"
      v-if="isLoading"
    >
      <button v-if="deviceFound === false" @click="() => checkDevice(true)">
        Plug-In Carplay Dongle and Press
      </button>
      <div v-if="deviceFound === true" class="loading-spinner">
        <div class="spinner"></div>
      </div>
    </div>
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
}

.loading-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;

  .loading-spinner {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .spinner {
    border: 5px solid #f3f3f3;
    border-top: 5px solid #3498db;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
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