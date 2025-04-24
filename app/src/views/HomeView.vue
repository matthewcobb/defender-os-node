<template>
  <div class="home-view">
    <div class="battery-status" :class="{ 'disconnected': error }" @click="handleErrorClick">
      <LeisureBatteryPanel
        :batteryData="batteryData"
        :error="error"
      />
      <SolarPanel
        :solarData="solarData"
        :error="error"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { apiService } from '../features/system/services/api';
import SolarPanel from '../components/SolarPanel.vue';
import LeisureBatteryPanel from '../components/LeisureBatteryPanel.vue';
import { useToast } from '../features';

// Debug flag - set to true to use mock data instead of API calls
const USE_MOCK_DATA = true;

const error = ref('Connecting...');
const solarData = ref({});
const batteryData = ref({});
let intervalId: number | null = null;

// Use the global toast
const { error: showError, success: showSuccess } = useToast();

// Mock data for debug mode
const mockRenogyData = [
  {
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
  },
  {
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
  }
];

const fetchData = async () => {
  try {
    if (USE_MOCK_DATA) {
      // Use mock data
      solarData.value = mockRenogyData[0];
      batteryData.value = mockRenogyData[1];
      error.value = '';
    } else {
      // Use real API data
      const response = await apiService.getRenogyData();
      if (Array.isArray(response) && response.length >= 2) {
        // First object is solar controller data
        solarData.value = response[0];
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

const handleErrorClick = () => {
  if (error.value) {
    showError(error.value);
  } else {
    showSuccess('Connected');
  }
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
.battery-status {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.5rem;
}
</style>