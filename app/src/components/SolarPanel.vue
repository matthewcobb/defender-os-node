<template>
  <div class="panel solar">
    <div class="panel-header">
      <h2>Solar</h2>
      <Sun class="solar" :size="32" />
    </div>
    <div v-if="error" class="error-state">
      <p>Connecting...</p>
    </div>
    <div v-else>
      <LevelIndicator :percentage="solarPowerPercentage" type="solar">
        {{ solarData?.pv_power || '0' }}W
      </LevelIndicator>
      <div class="grid justify-between">
        <div class="stat">
          <h4>Voltage</h4>
          <p class="value">
            <BatteryMedium :size="20" class="icon" />
            {{ solarData?.pv_voltage || '0' }}V
          </p>
        </div>
        <div class="stat">
          <h4>Load</h4>
          <p class="value">
            <ArrowRight :size="20" class="icon" />
            {{ solarData?.load_power || '0' }}A
          </p>
        </div>
        <div class="stat">
          <h4>Today</h4>
          <p class="value">
            <Calendar :size="20" class="icon" />
            {{ solarData?.power_generation_today || '0' }}Wh
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Sun, BatteryMedium, ArrowRight, Calendar } from 'lucide-vue-next';
import LevelIndicator from './LevelIndicator.vue';

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
</script>

<style lang="scss" scoped>
// Component-specific styles only
</style>