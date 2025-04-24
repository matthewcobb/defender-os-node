<template>
  <div class="battery-full-view">
    <FullScreenDisplay
      :startFullscreen="true"
      :disableCollapse="true"
      :padding="true"
      @close="closeView"
    >
      <div class="panel-header">
        <h1>Battery Details</h1>
      </div>

      <div v-if="error" class="error-state">
        <p>{{ error }}</p>
      </div>
      <div v-else class="battery-data">
        <LevelIndicator
          :percentage="batteryPercentage"
          type="leisure"
          :charging="isCharging"
        >
          {{ batteryPercentage }}%
        </LevelIndicator>

        <div class="stats-grid">
          <div class="stat">
            <h4>State</h4>
            <p class="value">{{ isCharging ? 'Charging' : isFullyCharged ? 'Fully Charged' : 'Discharging' }}</p>
          </div>

          <div class="stat">
            <h4>Voltage</h4>
            <p class="value">{{ batteryData?.voltage || '0' }}V</p>
          </div>

          <div class="stat">
            <h4>Current</h4>
            <p class="value">{{ batteryData?.current || '0' }}A</p>
          </div>

          <div class="stat">
            <h4>{{ isCharging ? 'Time until full' : 'Time until empty' }}</h4>
            <p class="value">
              {{ isFullyCharged ? '--' : isCharging ?
                batteryData?.time_remaining_to_charge :
                batteryData?.time_remaining_to_empty }}
            </p>
          </div>

          <div class="stat" v-if="batteryData?.cell_count">
            <h4>Cell Voltages</h4>
            <div class="cell-voltages">
              <div v-for="i in cellCount" :key="`cell-${i}`" class="cell-voltage">
                <span>Cell {{ i }}:</span>
                <span>{{ batteryData[`cell_voltage_${i-1}`] || '0' }}V</span>
              </div>
            </div>
          </div>

          <div class="stat" v-if="batteryData?.sensor_count">
            <h4>Temperatures</h4>
            <div class="temperatures">
              <div v-for="i in sensorCount" :key="`temp-${i}`" class="temperature">
                <span>Sensor {{ i }}:</span>
                <span>{{ batteryData[`temperature_${i-1}`] || '0' }}°C</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </FullScreenDisplay>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import FullScreenDisplay from '../components/FullScreenDisplay.vue';
import LevelIndicator from '../components/LevelIndicator.vue';
import { apiService } from '../features/system/services/api';

// Define interface for battery data
interface BatteryData {
  function?: string;
  cell_count?: number;
  sensor_count?: number;
  current?: number;
  voltage?: number;
  time_remaining_to_charge?: string;
  time_remaining_to_empty?: string;
  pv_power?: number;
  load_power?: number;
  remaining_charge?: number;
  capacity?: number;
  model?: string;
  device_id?: number;
  [key: string]: any; // For dynamic properties like cell_voltage_0, temperature_0, etc.
}

const router = useRouter();
const error = ref('Connecting...');
const batteryData = ref<BatteryData>({});
let intervalId: number | null = null;

// Mock data for debug mode - remove this when using real API data
const USE_MOCK_DATA = true;
const mockBatteryData = {
  "function": "READ",
  "cell_count": 4,
  "cell_voltage_0": 3.3,
  "cell_voltage_1": 3.3,
  "cell_voltage_2": 3.3,
  "cell_voltage_3": 3.3,
  "sensor_count": 4,
  "temperature_0": 11.0,
  "temperature_1": 11.0,
  "temperature_2": 11.0,
  "temperature_3": 11.0,
  "current": 0.48,
  "voltage": 13.4,
  "time_remaining_to_charge": "1hr 40mins",
  "time_remaining_to_empty": "1hr 40mins",
  "pv_power": 10,
  "load_power": 10,
  "remaining_charge": 40,
  "capacity": 99.99,
  "model": "RBT100LFP12S-G",
  "device_id": 247
};

const isFullyCharged = computed(() => {
  return (batteryData.value?.remaining_charge ?? 0) > 99.5;
});

const batteryPercentage = computed(() => {
  return Math.round(parseFloat(String(batteryData.value?.remaining_charge ?? '0')));
});

const isCharging = computed(() => {
  return (batteryData.value?.current ?? 0) > 0;
});

const cellCount = computed(() => {
  return batteryData.value?.cell_count ?? 0;
});

const sensorCount = computed(() => {
  return batteryData.value?.sensor_count ?? 0;
});

const fetchData = async () => {
  try {
    if (USE_MOCK_DATA) {
      // Use mock data
      batteryData.value = mockBatteryData;
      error.value = '';
    } else {
      // Use real API data
      const response = await apiService.getRenogyData();
      if (Array.isArray(response) && response.length >= 2) {
        // Second object is battery data
        batteryData.value = response[1];
        error.value = '';
      } else {
        throw new Error('Invalid data format received');
      }
    }
  } catch (err: any) {
    error.value = err?.message || 'Connection error';
  }
};

const closeView = () => {
  router.back();
};

onMounted(() => {
  fetchData();
  intervalId = window.setInterval(fetchData, 5000);
});

onUnmounted(() => {
  if (intervalId !== null) {
    clearInterval(intervalId);
  }
});
</script>

<style lang="scss" scoped>
.battery-full-view {
  width: 100%;
  height: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;

  h1 {
    font-size: 1.5rem;
    margin: 0;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.stat {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 0.5rem;
  padding: 1rem;

  h4 {
    margin-top: 0;
    opacity: 0.7;
    font-weight: normal;
    margin-bottom: 0.5rem;
  }

  .value {
    font-size: 1.25rem;
    font-weight: bold;
  }
}

.cell-voltages,
.temperatures {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;

  .cell-voltage,
  .temperature {
    display: flex;
    justify-content: space-between;
  }
}
</style>