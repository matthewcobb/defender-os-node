<template>
  <div class="panel solar">
    <div class="panel-header">
      <h2>Solar</h2>
      <Sun class="solar" :size="32" />
    </div>
    <div v-if="error" class="error-state">
      <p>Connecting...</p>
    </div>
    <div v-else class="solar-info">
      <div class="level-container">
        <div class="level" :style="{ width: solarPowerPercentage + '%' }">
          {{ solarData?.pv_power || '0' }}W
        </div>
      </div>
      <div class="solar-details">
        <div class="stat">
          <span class="label">Voltage</span>
          <span class="value">
            <BatteryMedium :size="20" class="icon" />
            {{ solarData?.pv_voltage || '0' }}V
          </span>
        </div>
        <div class="stat">
          <span class="label">Current</span>
          <span class="value">
            <ArrowRight :size="20" class="icon" />
            {{ solarData?.pv_current || '0' }}A
          </span>
        </div>
        <div class="stat">
          <span class="label">Today</span>
          <span class="value">
            <Calendar :size="20" class="icon" />
            {{ solarData?.power_generation_today || '0' }}Wh
          </span>
        </div>
      </div>
      <div class="additional-details">
        <div class="stat">
          <span class="label">Status</span>
          <span class="value">
            <ActivitySquare :size="20" class="icon" />
            {{ chargingStatus }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Sun, BatteryMedium, ArrowRight, Calendar, ActivitySquare } from 'lucide-vue-next';

const props = defineProps({
  solarData: {
    type: Object,
    default: () => ({})
  },
  error: {
    type: String,
    default: ''
  }
});

// Calculate power percentage (for display bar)
// assuming max power is 400W, or use max_charging_power_today
const solarPowerPercentage = computed(() => {
  const currentPower = props.solarData?.pv_power || 0;
  const maxPower = props.solarData?.max_charging_power_today || 200;
  const percentage = (currentPower / maxPower) * 100;
  return Math.min(percentage, 100); // Cap at 100%
});

const chargingStatus = computed(() => {
  if (!props.solarData?.charging_status) return 'Unknown';

  const status = props.solarData.charging_status;
  switch (status) {
    case 'mppt':
      return 'MPPT';
    case 'boost':
      return 'Boost';
    case 'float':
      return 'Float';
    case 'equalization':
      return 'Equalization';
    default:
      return status.charAt(0).toUpperCase() + status.slice(1);
  }
});
</script>

<style lang="scss" scoped>
// Component-specific styles only
</style>