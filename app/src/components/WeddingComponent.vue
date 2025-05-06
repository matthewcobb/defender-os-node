<template>
  <FullScreenDisplay
    :start-fullscreen="true"
    :disable-collapse="true"
    @close="closeWedding"
  >
    <div class="wedding-container">
      <div class="slideshow-container">
        <transition-group name="fade">
          <template v-for="(media, index) in mediaItems" :key="media.src">
            <img
              v-if="media.type === 'image'"
              :src="media.src"
              v-show="currentMediaIndex === index"
              alt="Wedding announcement background"
            />
            <video
              v-else-if="media.type === 'video'"
              :src="media.src"
              v-show="currentMediaIndex === index"
              autoplay
              muted
              loop
              playsinline
            ></video>
          </template>
        </transition-group>
      </div>
      <div class="wedding-content">
        <p class="fgColor-muted">
          May 10th, 2025
        </p>
        <h1 class="title">
          WE'RE GETTING MARRIED
        </h1>
        <div class="message">
          <p>
            Your carriage awaits, can't wait to see you on the isle! You look <b>GORGEOUS!</b>
          </p>
          <p>
            Love, Matt x
          </p>
        </div>
        <button class="btn btn-lg" @click="closeWedding">Continue</button>
      </div>
    </div>
  </FullScreenDisplay>
</template>

<script setup lang="ts">
import { defineEmits, ref, onMounted, onUnmounted } from 'vue';
import FullScreenDisplay from './FullScreenDisplay.vue';

const emit = defineEmits(['close']);

// Media items (images and videos) for the slideshow
interface MediaItem {
  type: 'image' | 'video';
  src: string;
}

const mediaItems = ref<MediaItem[]>([
  {
    type: 'image',
    src: new URL('../assets/landy.webp', import.meta.url).href
  },
  {
    type: 'video',
    src: new URL('../assets/coconut.mp4', import.meta.url).href
  }
]);

const currentMediaIndex = ref(0);
let slideInterval: number | null = null;

const rotateMedia = () => {
  currentMediaIndex.value = (currentMediaIndex.value + 1) % mediaItems.value.length;
};

onMounted(() => {
  slideInterval = window.setInterval(rotateMedia, 8000);
});

onUnmounted(() => {
  if (slideInterval !== null) {
    clearInterval(slideInterval);
  }
});

const closeWedding = () => {
  emit('close');
};
</script>

<style lang="scss" scoped>
p {
  font-size: 1.75rem;
}
.wedding-container {
  width: 100%;
  height: 100%;
  display: flex;
  position: relative;
}

.slideshow-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;

  img, video {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center right;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.wedding-content {
  width: 90%;
  max-width: 100%;
  padding: 2.5rem;
  background-image: linear-gradient(140deg, rgba(0, 0, 0, 0.9) 20%, rgba(0, 0, 0, 0) 65%);
  position: relative;
  z-index: 1;

  .title {
    font-size: 3rem;
    color: var(--dangeer);
    text-shadow: 0 0 10px var(--daeger);
    max-width: 50vw;
    margin-top: 1rem;
  }
}

.message {
  margin: 0.5rem 0 1rem 0;
  line-height: 1.6;
  width: 50vw;

  p {
    margin: 0.5rem 0;
  }
}
</style>