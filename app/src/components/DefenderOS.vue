<template>
  <div class="defender-os">
    <TopBar />
    <nav class="tab-nav panel">
      <router-link v-for="tab in tabs" :key="tab.path" :to="tab.path" class="tab">
        <component :is="tab.icon" :size="32" />
      </router-link>
      <router-link v-if="weddingModeEnabled" to="/wedding" class="tab wedding-tab">
        <Heart :size="32" />
      </router-link>
    </nav>
    <div class="view-container">
      <router-view v-slot="{ Component, route }">
        <transition :name="transitionName">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import TopBar from './TopBar.vue';
import { CarFront, Bolt, Info, Video, Heart } from 'lucide-vue-next';
import { useRoute } from 'vue-router';
import { watch, ref, computed, onMounted } from 'vue';

// Define tabs with paths and icons in one place
const tabs = [
  { path: '/home', icon: CarFront },
  { path: '/settings', icon: Bolt },
  { path: '/reverse', icon: Video },
  { path: '/about', icon: Info }
];

// Check if wedding mode is enabled
const weddingModeEnabled = ref(false);

onMounted(() => {
  // Check if wedding mode is enabled in localStorage
  const savedWeddingMode = localStorage.getItem('weddingMode');

  // If no saved setting, default to true (wedding mode on)
  if (savedWeddingMode === null) {
    weddingModeEnabled.value = true;
    // Save this default setting
    localStorage.setItem('weddingMode', 'true');
  } else {
    weddingModeEnabled.value = savedWeddingMode === 'true';
  }

  // Listen for changes to wedding mode setting
  window.addEventListener('storage', (event) => {
    if (event.key === 'weddingMode') {
      weddingModeEnabled.value = event.newValue === 'true';
    }
  });
});

// Define tab routes based on the tabs array
const tabRoutes = computed(() => tabs.map(tab => tab.path));

// Track navigation for transitions
const route = useRoute();
const previousPath = ref('');

// Determine transition direction based on navigation
const transitionName = computed(() => {
  // If we don't have a previous path, just fade
  if (!previousPath.value) {
    return;
  }

  // Find indices in tab routes
  const currentIndex = tabRoutes.value.indexOf(route.path);
  const previousIndex = tabRoutes.value.indexOf(previousPath.value);

  // Only apply directional transitions for tab navigation
  if (currentIndex >= 0 && previousIndex >= 0) {
    return currentIndex > previousIndex ? 'nav-next' : 'nav-prev';
  }
});

// Track route changes to determine direction
watch(() => route.path, (_, oldPath) => {
  if (oldPath) {
    previousPath.value = oldPath;
  }
}, { immediate: true });

// DefenderOS component serves as a container for various subpages
</script>

<style lang="scss" scoped>
.defender-os {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(-45deg, #234432, #44534A, #202A24, #0e1310);
  background-size: 400% 400%;
  color: white;
  overflow: hidden;
  border-radius: 1rem;

  @keyframes gradient {
    0% {
      background-position: 0% 50%;
    }

    50% {
      background-position: 100% 50%;
    }

    100% {
      background-position: 0% 50%;
    }
  }
}

.tab-nav {
  position: absolute;
  width: auto;
  bottom: 0.5rem;
  left: 0.5rem;
  right: 0.5rem;
  border-radius: 0.75rem;
  padding: 0 1rem;
  display: flex;
  justify-content: space-around;
  backdrop-filter: blur(1rem);
  z-index: 10;
}

.tab {
  padding: 1rem 1rem;
  border-bottom: 2px solid transparent;
  text-decoration: none;
  color: var(--fgColor-muted);
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s, color 0.2s;

  &:hover {
    background-color: var(--panel-bg);
  }

  &.router-link-active {
    border-color: var(--primary);
    color: var(--primary);
  }
}

.view-container {
  width: 100%;
  height: calc(100vh - var(--top-bar-height)); /* Fills the remaining vertical space */
  position: relative;
}
</style>