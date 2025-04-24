<template>
  <div class="solar-full-view">
    <FullScreenDisplay
      :startFullscreen="true"
      :disableCollapse="true"
      :padding="true"
      @close="closeView"
    >
      <div class="panel-header">
        <h1>Solar Details</h1>
      </div>

      <div v-if="error" class="error-state">
        <p>{{ error }}</p>
      </div>
      <div v-else class="solar-data">
        <LevelIndicator :percentage="solarPowerPercentage" type="solar">
          {{ solarData?.pv_power || '0' }}W
        </LevelIndicator>

        <div class="stats-grid">
          <div class="stat">
            <h4>Current Status</h4>
            <p class="value">{{ formatChargingStatus(solarData?.charging_status) }}</p>
          </div>

          <div class="stat">
            <h4>PV Voltage</h4>
            <p class="value">{{ solarData?.pv_voltage || '0' }}V</p>
          </div>

          <div class="stat">
            <h4>PV Current</h4>
            <p class="value">{{ solarData?.pv_current || '0' }}A</p>
          </div>

          <div class="stat">
            <h4>Load Power</h4>
            <p class="value">{{ solarData?.load_power || '0' }}W</p>
          </div>

          <div class="stat">
            <h4>Power Today</h4>
            <p class="value">{{ solarData?.power_generation_today || '0' }}Wh</p>
          </div>

          <div class="stat">
            <h4>Total Generation</h4>
            <p class="value">{{ formatTotalPower(solarData?.power_generation_total) }}</p>
          </div>

          <div class="stat">
            <h4>Max Charging Today</h4>
            <p class="value">{{ solarData?.max_charging_power_today || '0' }}W</p>
          </div>

          <div class="stat">
            <h4>Controller Temperature</h4>
            <p class="value">{{ solarData?.controller_temperature || '0' }}°C</p>
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

// Define interface for solar data
interface SolarData {
  function?: string;
  model?: string;
  device_id?: number;
  battery_percentage?: number;
  battery_voltage?: number;
  battery_current?: number;
  battery_temperature?: number;
  controller_temperature?: number;
  load_status?: string;
  load_voltage?: number;
  load_current?: number;
  load_power?: number;
  pv_voltage?: number;
  pv_current?: number;
  pv_power?: number;
  max_charging_power_today?: number;
  max_discharging_power_today?: number;
  charging_amp_hours_today?: number;
  discharging_amp_hours_today?: number;
  power_generation_today?: number;
  power_consumption_today?: number;
  power_generation_total?: number;
  charging_status?: string;
  battery_type?: string;
}

const router = useRouter();
const error = ref('Connecting...');
const solarData = ref<SolarData>({});
let intervalId: number | null = null;

// Mock data for debug mode - remove this when using real API data
const USE_MOCK_DATA = true;
const mockSolarData = {
  "function": "READ",
  "model": "RBC50D1S-G1",
  "device_id": 96,
  "battery_percentage": 100,
  "battery_voltage": 13.4,
  "battery_current": 20,
  "battery_temperature": 25,
  "controller_temperature": 21,
  "load_status": "off",
  "load_voltage": 12.5,
  "load_current": 0.0,
  "load_power": 10,
  "pv_voltage": 18.7,
  "pv_current": 0.45,
  "pv_power": 10,
  "max_charging_power_today": 200,
  "max_discharging_power_today": 0,
  "charging_amp_hours_today": 4,
  "discharging_amp_hours_today": 0,
  "power_generation_today": 54,
  "power_consumption_today": 0,
  "power_generation_total": 39664,
  "charging_status": "mppt",
  "battery_type": "lithium"
};

// Calculate power percentage (for display bar)
// assuming max power is 400W, or use max_charging_power_today
const solarPowerPercentage = computed(() => {
  const currentPower = solarData.value?.pv_power || 0;
  const maxPower = solarData.value?.max_charging_power_today || 200;
  const percentage = (currentPower / maxPower) * 100;
  return Math.min(percentage, 100); // Cap at 100%
});

// Format the charging status to be more readable
const formatChargingStatus = (status: string | undefined) => {
  if (!status) return 'Unknown';

  // Convert 'mppt' to 'MPPT' and capitalize other statuses
  if (status.toLowerCase() === 'mppt') {
    return 'MPPT Charging';
  }

  // Capitalize first letter of each word
  return status
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Format the total power generation
const formatTotalPower = (value: number | undefined) => {
  if (!value) return '0 Wh';

  // If over 1000 kWh, show as MWh
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(2)} MWh`;
  }

  // If over 1000 Wh, show as kWh
  if (value >= 1000) {
    return `${(value / 1000).toFixed(2)} kWh`;
  }

  return `${value} Wh`;
};

const fetchData = async () => {
  try {
    if (USE_MOCK_DATA) {
      // Use mock data
      solarData.value = mockSolarData;
      error.value = '';
    } else {
      // Use real API data
      const response = await apiService.getRenogyData();
      if (Array.isArray(response) && response.length >= 1) {
        // First object is solar controller data
        solarData.value = response[0];
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
.solar-full-view {
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
</style>