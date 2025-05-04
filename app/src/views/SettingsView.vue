<template>
  <div class="view">
    <div class="settings-view">
      <WifiPanel />
      <SystemPanel />
      <CameraPanel />
    </div>
  </div>
</template>

<script setup lang="ts">
import SystemPanel from '../components/settings/SystemPanel.vue';
import CameraPanel from '../components/settings/CameraPanel.vue';
import WifiPanel from '../components/settings/WifiPanel.vue';
</script>

<style lang="scss" scoped>
.settings-view {
  display: grid;
  gap: 0.5rem;
}
</style>