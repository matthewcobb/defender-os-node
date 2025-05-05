<template>
  <div class="top-bar">
    <div class="menu">
      <p class="app-name">
        DEFENDER<span class="fgColor-muted">OS</span>
      </p>
      <div class="menu-items">
        <CpuTemp />
        <WifiIcon
          :is-active="isMenuActive('wifi-status')"
          @menu-toggle="handleMenuToggle"
        />
      </div>
    </div>
    <div class="menu-container" v-if="activeMenuItem">
      <Transition name="fade" appear>
        <div v-if="activeMenuItem.isOpen" class="menu-overlay" @click.stop="closeMenuItem"></div>
      </Transition>
      <Transition name="slide-down" appear>
        <div v-if="activeMenuItem.isOpen" class="menu-content">
          <div class="menu-panel">
            <div class="menu-header">
              <h4>{{ menuTitles[activeMenuItem.content.component] || activeMenuItem.title }}</h4>
              <div class="menu-close" @click.stop="closeMenuItem">
                <X />
              </div>
            </div>
            <div class="menu-body">
              <component
                :is="resolveComponent(activeMenuItem.content.component)"
                v-bind="activeMenuItem.content.props"
              />
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import WifiIcon from './WifiIcon.vue';
import CpuTemp from './CpuTemp.vue';
import { useMenuItems } from '../features/ui';
import { X } from 'lucide-vue-next';
import WifiStatus from './dropdowns/WifiStatus.vue';

const { activeMenuItem, openMenuItem, closeMenuItem } = useMenuItems();

// Menu titles mapping
const menuTitles: Record<string, string> = {
  'wifi-status': 'WiFi Status'
};

// Check if a specific menu is active
const isMenuActive = (menuName: string) => {
  return activeMenuItem.value?.content.component === menuName && activeMenuItem.value?.isOpen;
};

// Handle menu toggle events from child components
const handleMenuToggle = (menuName: string) => {
  if (isMenuActive(menuName)) {
    closeMenuItem();
    return;
  }

  // Open the menu with the specified component
  openMenuItem(menuTitles[menuName] || menuName, {
    component: menuName,
    props: {}
  });
};

// Close menu when clicking outside the TopBar
const handleOutsideClick = (event: MouseEvent) => {
  // Check if click is outside TopBar
  if (activeMenuItem.value?.isOpen && !event.composedPath().includes(document.querySelector('.top-bar') as HTMLElement)) {
    closeMenuItem();
  }
};

// Add global click handler
onMounted(() => {
  document.addEventListener('click', handleOutsideClick);
});

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick);
});

// Resolve component name to actual component
const resolveComponent = (componentName: string) => {
  const components: Record<string, any> = {
    'wifi-status': WifiStatus
    // Add more components as needed
  };

  return components[componentName] || null;
};
</script>

<style lang="scss" scoped>

.top-bar {
  position: relative;

  .menu {
    position: relative;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: var(--top-bar-bg);
    padding: 0 1rem;
    height: var(--top-bar-height);
    z-index: 100;

    .menu-items {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

  .app-name {
    font-weight: 100;
    letter-spacing: 0.1rem;
    margin: 0;
    }
  }

  .menu-container {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 0;
    overflow: visible;
  }

  .menu-overlay {
    position: absolute;
    top: var(--top-bar-height);
    left: 0;
    width: 100%;
    height: calc(100vh - var(--top-bar-height));
    background-color: var(--translucent);
    z-index: 90;
    backdrop-filter: blur(1rem);
  }

  .menu-content {
    position: absolute;
    top: var(--top-bar-height);
    max-height: calc(100vh - var(--top-bar-height));
    overflow:auto;
    left: 0;
    width: 100%;
    z-index: 91;
  }

  .menu-panel {
    width: 100%;
    background-color: var(--tooltip-bg);
    border-radius: 0 0 0.5rem 0.5rem;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    padding: 1rem;
    box-sizing: border-box;
  }

  .menu-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;

    h4 {
      margin: 0;
    }

    .menu-close {
      cursor: pointer;
    }
  }
}
</style>