<template>
  <div class="solar-view">
    <FullScreenDisplay
      :startFullscreen="true"
      :disableCollapse="true"
      :padding="true"
      @close="closeView"
    >
      <div class="panel-header">
        <h1>Solar Details</h1>
      </div>

      <div v-if="!renogyStore.devicesReady" class="error-state">
        <p>Connecting...</p>
      </div>
      <div v-else class="solar-data">
        <LevelIndicator :percentage="renogyStore.solarPowerPercentage" type="solar">
          {{ renogyStore.data?.pv_power || '0' }}W
        </LevelIndicator>

        <div class="stats-grid">
          <div class="stat">
            <h4>Current Status</h4>
            <p class="value">{{ renogyStore.formatChargingStatus(renogyStore.data?.charger_status) }}</p>
          </div>

          <div class="stat">
            <h4>PV Voltage</h4>
            <p class="value">{{ renogyStore.data?.pv_voltage || '0' }}V</p>
          </div>

          <div class="stat">
            <h4>PV Current</h4>
            <p class="value">{{ renogyStore.data?.pv_current || '0' }}A</p>
          </div>

          <div class="stat">
            <h4>Load Power</h4>
            <p class="value">{{ renogyStore.data?.load_power || '0' }}W</p>
          </div>

          <div class="stat">
            <h4>Power Today</h4>
            <p class="value">{{ renogyStore.data?.power_generation_today || '0' }}Wh</p>
          </div>

          <div class="stat">
            <h4>Total Generation</h4>
            <p class="value">{{ renogyStore.formatTotalPower(renogyStore.data?.power_generation_total) }}</p>
          </div>

          <div class="stat">
            <h4>Max Charging Today</h4>
            <p class="value">{{ renogyStore.data?.max_charging_power_today || '0' }}W</p>
          </div>

          <div class="stat">
            <h4>Controller Temperature</h4>
            <p class="value">{{ renogyStore.data?.controller_temperature || '0' }}°C</p>
          </div>
        </div>
      </div>
    </FullScreenDisplay>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useRenogyStore } from '../stores/renogyStore';
import FullScreenDisplay from '../components/FullScreenDisplay.vue';
import LevelIndicator from '../components/LevelIndicator.vue';

const router = useRouter();
const renogyStore = useRenogyStore();

const closeView = () => {
  router.back();
};

onMounted(() => {
  renogyStore.init();
});

onUnmounted(() => {
  renogyStore.cleanup();
});
</script>

<style lang="scss" scoped>
.solar-view {
  width: 100%;
  height: 100%;
}

.panel-header {
  text-align: center;
  margin-bottom: 1rem;

  h1 {
    font-size: 1.5rem;
    font-weight: 500;
    margin: 0;
  }
}

.error-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80%;
  flex-direction: column;
  text-align: center;
  color: var(--color-error);

  p {
    font-size: 1.2rem;
  }
}

.solar-data {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1.5rem;
}

.stat {
  h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.9rem;
    color: var(--color-text-secondary);
    font-weight: 400;
  }

  .value {
    font-size: 1.2rem;
    font-weight: 500;
    margin: 0;
  }
}
</style>