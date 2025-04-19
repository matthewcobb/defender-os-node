<template>
  <div class="home-view">
    <div class="battery-status" :class="{ 'disconnected': error }" @click="handleErrorClick">
      <SolarPanel
        :solarData="solarData"
        :error="error"
      />
      <LeisureBatteryPanel
        :batteryData="batteryData"
        :error="error"
      />
    </div>
    <ToastMessage
      :show="showToast"
      :text="toastMessage"
      :type="toastType"
      @update:show="showToast = $event"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { apiService } from '../services/api';
import SolarPanel from '../components/SolarPanel.vue';
import LeisureBatteryPanel from '../components/LeisureBatteryPanel.vue';
import ToastMessage from '../components/ToastMessage.vue';

const error = ref('Connecting...');
const solarData = ref({});
const batteryData = ref({});
let intervalId: number | null = null;

// Toast state
const showToast = ref(false);
const toastMessage = ref('');
const toastType = ref<'success' | 'error'>('success');

const displayToast = (message: string, type: 'success' | 'error') => {
  toastMessage.value = message;
  toastType.value = type;
  showToast.value = true;
};

const fetchData = async () => {
  try {
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
  } catch (err: any) {
    error.value = err?.message || 'Connection error';
  }
};

const handleErrorClick = () => {
  if (error.value) {
    displayToast(error.value, 'error');
  } else {
    displayToast('Connected', 'success');
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
  gap: 1rem;

  &.disconnected {
    opacity: 0.7;
  }
}
</style>