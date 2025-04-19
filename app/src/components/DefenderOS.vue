<template>
  <div class="defender-os">
    <TopBar />
    <nav class="tab-nav">
      <router-link to="/home" class="tab">Home</router-link>
      <router-link to="/settings" class="tab">Settings</router-link>
      <router-link to="/about" class="tab">About</router-link>
    </nav>
    <main class="content">
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import TopBar from './TopBar.vue';
// DefenderOS component serves as a container for various subpages
</script>

<style lang="scss" scoped>
.defender-os {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(-45deg, #7c9386, #44534A, #202A24, #0e1310);
  background-size: 400% 400%;
  animation: gradient 15s ease infinite;
  color: white;
  border-radius: 1rem;
  overflow: hidden;

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

nav {
  position: absolute;
  bottom: 0.5rem;
  left: 0.5rem;
  right: 0.5rem;
  border-radius: 0.5rem;
  padding: 0 1rem;
  display: flex;
  gap: 1rem;
  background: var(--panel-bg);
  box-shadow: var(--box-shadow);
  backdrop-filter: blur(0.5rem);
}

.tab {
  padding: 1rem 0rem;
  border-bottom: 2px solid transparent;
  text-decoration: none;
  color: #ccc;
  font-weight: 500;
  display: inline-block;
  transition: background-color 0.2s, color 0.2s;

  &:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }

  &.router-link-active {
    border-color: var(--primary);
    color: white;
  }
}

.content {
  flex: 1;
  padding: 1rem;
  width: 100%;
  overflow: hidden;
  box-sizing: border-box;
}
</style>