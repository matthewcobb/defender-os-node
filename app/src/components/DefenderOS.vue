<template>
  <div class="defender-os">
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
// DefenderOS component serves as a container for various subpages
</script>

<style lang="scss" scoped>
.defender-os {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #222;
  color: white;
  border-radius: 1rem;
  overflow: hidden;
}

.tab-nav {
  position: absolute;
  bottom: 1rem;
  width: 100%;
  background-color: #333;
}

.tab {
  padding: 0.5rem 1rem;
  margin-right: 0.5rem;
  border-radius: 4px;
  text-decoration: none;
  color: #ccc;
  font-weight: bold;
  transition: background-color 0.2s, color 0.2s;

  &:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }

  &.router-link-active {
    background-color: #4CAF50;
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