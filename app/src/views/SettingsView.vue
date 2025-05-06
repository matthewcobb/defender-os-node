<template>
  <div class="view">
    <main class="settings-view">
      <SystemPanel />
      <CameraPanel />
    </main>
  </div>
</template>

<script setup lang="ts">
import SystemPanel from '../components/settings/SystemPanel.vue';
import CameraPanel from '../components/settings/CameraPanel.vue';
</script>

<style lang="scss" scoped>
.settings-view {
  display: grid;
  gap: 0.5rem;
}
</style>