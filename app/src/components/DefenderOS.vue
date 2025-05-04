<template>
  <div class="defender-os">
    <TopBar />
    <nav class="tab-nav panel">
      <router-link to="/home" class="tab">
        <CarFront :size="32" />
      </router-link>
      <router-link to="/settings" class="tab">
        <Bolt :size="32" />
      </router-link>
      <router-link to="/reverse" class="tab">
        <Video :size="32" />
      </router-link>
      <router-link to="/about" class="tab">
        <Info :size="32" />
      </router-link>
    </nav>
    <main class="content">
      <router-view v-slot="{ Component, route }">
        <transition :name="transitionName">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import TopBar from './TopBar.vue';
import { CarFront, Bolt, Info, Video } from 'lucide-vue-next';
import { useRoute } from 'vue-router';
import { watch, ref, computed } from 'vue';

// Define tab routes in order of appearance in the UI
const tabRoutes = ['/home', '/settings', '/reverse', '/about'];

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
  const currentIndex = tabRoutes.indexOf(route.path);
  const previousIndex = tabRoutes.indexOf(previousPath.value);

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
  animation: loading 0.4s ease-out, gradient 15s ease infinite;

  @keyframes loading {
    from {
      transform: translateX(-100%);
    }
    to {
      transform: translateX(0);
    }
  }

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

.content {
  width: 100%;
  height: calc(100vh - var(--top-bar-height)); /* Fills the remaining vertical space */
  position: relative;
}
</style>