<template>
  <div class="panel leisure">
    <div class="panel-header">
      <h2>Battery</h2>
      <BatteryMedium class="leisure" :size="32" />
    </div>
    <div v-if="error" class="error-state">
      <p>Connecting...</p>
    </div>
    <div v-else class="battery-info">
      <div class="level-container">
        <div class="level" :style="{ width: batteryPercentage + '%' }">
          {{ batteryPercentage }}%
        </div>
      </div>
      <div class="battery-details">
        <div class="stat">
          <span class="label">Voltage</span>
          <span class="value">
            <Gauge :size="16" class="icon" />
            {{ batteryData?.voltage || '0' }}V
          </span>
        </div>
        <div class="stat">
          <span class="label">Current</span>
          <span class="value">
            <ArrowRight :size="16" class="icon" />
            {{ batteryData?.current || '0' }}A
          </span>
        </div>

        <div class="stat">
          <span class="label">Capacity</span>
          <span class="value">
            <BarChart2 :size="16" class="icon" />
            {{ batteryData?.capacity || '0' }}%
          </span>
        </div>
        <div class="stat">
          <span class="label">Temp</span>
          <span class="value">
            <Thermometer :size="16" class="icon" />
            {{ averageTemperature }}°C
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { BatteryMedium, BatteryCharging, Gauge, ArrowRight, BarChart2, Thermometer } from 'lucide-vue-next';

const props = defineProps({
  batteryData: {
    type: Object,
    default: () => ({})
  },
  error: {
    type: String,
    default: ''
  }
});

const batteryPercentage = computed(() => {
  return Math.round(parseFloat(props.batteryData?.remaining_charge || '0'));
});

const averageTemperature = computed(() => {
  if (!props.batteryData) return '0';

  const temps = [];
  for (let i = 0; i < (props.batteryData.sensor_count || 0); i++) {
    const temp = props.batteryData[`temperature_${i}`];
    if (temp !== undefined) {
      temps.push(parseFloat(temp));
    }
  }

  if (temps.length === 0) return '0';

  const avg = temps.reduce((sum, temp) => sum + temp, 0) / temps.length;
  return avg.toFixed(1);
});
</script>

<style lang="scss" scoped>
// Component-specific styles only
</style>