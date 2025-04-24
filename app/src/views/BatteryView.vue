<template>
  <div class="battery-view">
    <FullScreenDisplay
      :startFullscreen="true"
      :disableCollapse="true"
      :padding="true"
      @close="closeView"
    >
      <div class="panel-header">
        <h1>Battery Details</h1>
      </div>

      <div v-if="renogyStore.error" class="error-state">
        <p>{{ renogyStore.error }}</p>
      </div>
      <div v-else class="battery-data">
        <LevelIndicator
          :percentage="renogyStore.batteryPercentage"
          type="leisure"
          :charging="renogyStore.isCharging"
        >
          {{ renogyStore.batteryPercentage }}%
        </LevelIndicator>

        <div class="stats-grid">
          <div class="stat">
            <h4>State</h4>
            <p class="value">{{ renogyStore.isCharging ? 'Charging' : renogyStore.isFullyCharged ? 'Fully Charged' : 'Discharging' }}</p>
          </div>

          <div class="stat">
            <h4>Voltage</h4>
            <p class="value">{{ renogyStore.batteryData?.voltage || '0' }}V</p>
          </div>

          <div class="stat">
            <h4>Current</h4>
            <p class="value">{{ renogyStore.batteryData?.current || '0' }}A</p>
          </div>

          <div class="stat">
            <h4>{{ renogyStore.isCharging ? 'Time until full' : 'Time until empty' }}</h4>
            <p class="value">
              {{ renogyStore.isFullyCharged ? '--' : renogyStore.isCharging ?
                renogyStore.batteryData?.time_remaining_to_charge :
                renogyStore.batteryData?.time_remaining_to_empty }}
            </p>
          </div>

          <div class="stat" v-if="renogyStore.batteryData?.cell_count">
            <h4>Cell Voltages</h4>
            <div class="cell-voltages">
              <div v-for="i in renogyStore.cellCount" :key="`cell-${i}`" class="cell-voltage">
                <span>Cell {{ i }}:</span>
                <span>{{ renogyStore.batteryData[`cell_voltage_${i-1}`] || '0' }}V</span>
              </div>
            </div>
          </div>

          <div class="stat" v-if="renogyStore.batteryData?.sensor_count">
            <h4>Temperatures</h4>
            <div class="temperatures">
              <div v-for="i in renogyStore.sensorCount" :key="`temp-${i}`" class="temperature">
                <span>Sensor {{ i }}:</span>
                <span>{{ renogyStore.batteryData[`temperature_${i-1}`] || '0' }}°C</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </FullScreenDisplay>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import FullScreenDisplay from '../components/FullScreenDisplay.vue';
import LevelIndicator from '../components/LevelIndicator.vue';
import { useRenogyStore } from '../stores/renogyStore';

const router = useRouter();
const renogyStore = useRenogyStore();

const closeView = () => {
  router.back();
};

onMounted(() => {
  renogyStore.startPolling();
});

onUnmounted(() => {
  renogyStore.stopPolling();
});
</script>

<style lang="scss" scoped>
.battery-view {
  width: 100%;
  height: 100%;
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

.battery-data {
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

.cell-voltages,
.temperatures {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.5rem;

  .cell-voltage,
  .temperature {
    display: flex;
    justify-content: space-between;
    font-size: 0.9rem;
  }
}
</style>