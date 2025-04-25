<template>
  <div class="home-view">
    <div class="battery-status" :class="{ 'disconnected': renogyStore.error }">
      <LeisureBatteryPanel
        :batteryData="renogyStore.batteryData"
        :error="renogyStore.error"
        @click="navigateToBattery"
      />
      <SolarPanel
        :solarData="renogyStore.solarData"
        :error="renogyStore.error"
        @click="navigateToSolar"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import SolarPanel from '../components/SolarPanel.vue';
import LeisureBatteryPanel from '../components/LeisureBatteryPanel.vue';
import { useToast } from '../features';
import { useRenogyStore } from '../stores/renogyStore';

const router = useRouter();
const renogyStore = useRenogyStore();
const { error: showError, success: showSuccess } = useToast();

const handleErrorClick = () => {
  if (renogyStore.error) {
    showError(renogyStore.error);
  } else {
    showSuccess('Connected');
  }
};

const navigateToBattery = () => {
  if (!renogyStore.error) {
    router.push({
      path: '/battery'
    });
  } else {
    handleErrorClick();
  }
};

const navigateToSolar = () => {
  if (!renogyStore.error) {
    router.push({
      path: '/solar'
    });
  } else {
    handleErrorClick();
  }
};

onMounted(() => {
  renogyStore.init();
});

onUnmounted(() => {
  renogyStore.cleanup();
});
</script>

<style lang="scss" scoped>
.battery-status {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.5rem;

  &.disconnected {
    opacity: 0.5;
  }
}
</style>