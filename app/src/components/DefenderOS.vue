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
      <router-link to="/about" class="tab">
        <Info :size="32" />
      </router-link>
    </nav>
    <main class="content">
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import TopBar from './TopBar.vue';
import { CarFront, Bolt, Info } from 'lucide-vue-next';
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
  animation: gradient 15s ease infinite;
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

.content {
  padding: 0.5rem;
  width: 100%;
  height: calc(100vh - var(--top-bar-height)); /* Fills the remaining vertical space */
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  padding-bottom: 5rem;
  &::-webkit-scrollbar {
    width: 0.75rem;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--translucent);
    border-radius: 0.5rem;
    border: 0.2rem solid var(--panel-bg);
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
}
</style>