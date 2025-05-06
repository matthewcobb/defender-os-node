<template>
  <div class="view">
    <main>
      <div class="battery-status" :class="{ 'disconnected': !renogyStore.devicesReady }">
        <LeisureBatteryPanel
          @click="navigateToBattery"
        />
        <SolarPanel
          @click="navigateToSolar"
        />
        <p v-if="renogyStore.devicesReady" class="last-updated">
          {{ renogyStore.formattedLastUpdatedTime }}
        </p>
      </div>
    </main>
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
  if (!renogyStore.devicesReady) {
    showError("Connecting... " + renogyStore.error);
  } else {
    showSuccess('Connected');
  }
};

const navigateToBattery = () => {
  if (!renogyStore.devicesReady) {
    router.push({
      path: '/battery'
    });
  } else {
    handleErrorClick();
  }
};

const navigateToSolar = () => {
  if (renogyStore.devicesReady) {
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

.last-updated {
  margin-top: 0.5rem;
  text-align: center;
  font-size: 0.75rem;
  color: var(--fgColor-muted);
}
</style>