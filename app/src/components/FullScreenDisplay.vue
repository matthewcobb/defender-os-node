<template>
  <div
    ref="container"
    class="fullscreen-display"
    :class="{ 'fullscreen': isFullscreen }"
  >
    <div class="content" :class="{ 'no-padding': !padding }">
      <slot></slot>
    </div>

    <div class="controls">
      <button class="close-btn" @click="onClose">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
          <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
      </button>
      <button v-if="!disableCollapse" class="fullscreen-btn" @click="toggleFullscreen">
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
import { ref, watch } from 'vue';

const emit = defineEmits(['close']);

const props = defineProps<{
  startFullscreen?: boolean; // Whether to start in fullscreen mode
  disableCollapse?: boolean; // Whether to disable the collapse button
  padding?: boolean; // Whether to disable the padding
}>();

const container = ref<HTMLDivElement | null>(null);
const isFullscreen = ref(false);

// Toggle fullscreen mode
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

// Close and emit event
const onClose = () => {
  emit('close');
};

// Set initial fullscreen state based on prop
watch(() => props.startFullscreen, (newValue) => {
  if (newValue !== undefined) {
    isFullscreen.value = newValue;
  }
}, { immediate: true });

// If disableCollapse is true and startFullscreen is true, force fullscreen
watch(() => props.disableCollapse, (newValue) => {
  if (newValue && props.startFullscreen) {
    isFullscreen.value = true;
  }
}, { immediate: true });
</script>

<style lang="scss" scoped>
.fullscreen-display {
  background-color: var(--full-screen-bg);
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 0.5rem;
  overflow: hidden;
  opacity: 0;
  animation: fadeIn 0.5s ease-in-out forwards;

  &.fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 9999;
    border-radius: 0;
  }

  .content {
    width: 100%;
    height: 100%;
    overflow: auto;
    padding: 2rem;
    box-sizing: border-box;
    &.no-padding {
      padding: 0;
    }
  }
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