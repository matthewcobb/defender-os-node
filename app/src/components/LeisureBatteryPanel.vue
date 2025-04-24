<template>
  <div class="panel leisure" :class="{ 'charging': isCharging }">
    <div class="panel-header">
      <h2>Battery</h2>
      <BatteryMedium class="leisure" :size="32" />
    </div>
    <div v-if="error" class="error-state">
      <p class="small">Connecting...</p>
    </div>
    <div v-else>
      <LevelIndicator
        :percentage="batteryPercentage"
        type="leisure"
        :charging="isCharging"
      >
        {{ batteryPercentage }}%
      </LevelIndicator>
      <div class="grid justify-between">
        <div class="stat">
          <div v-if="isFullyCharged">
            <h4>Battery is full</h4>
            <p class="value">
              <Gauge :size="24" class="icon" />
              --
            </p>
          </div>
          <div v-else-if="isCharging">
            <h4>Time until full</h4>
            <p class="value">
              <Gauge :size="24" class="icon" />
              {{ batteryData?.time_remaining_to_charge || '0' }}
            </p>
          </div>
          <div v-else>
            <h4>Time until empty</h4>
            <p class="value">
              <Gauge :size="24" class="icon" />
              {{ batteryData?.time_remaining_to_empty || '0' }}
            </p>
          </div>
        </div>
        <div class="stat text-right">
          <h4>Current</h4>
          <p class="value">
            <ArrowRight :size="24" class="icon" />
            {{ batteryData?.current || '0' }}A
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { BatteryMedium, Gauge, ArrowRight } from 'lucide-vue-next';
import LevelIndicator from './LevelIndicator.vue';

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

const isFullyCharged = computed(() => {
  return props.batteryData?.remaining_charge > 99.5;
});

const batteryPercentage = computed(() => {
  return Math.round(parseFloat(props.batteryData?.remaining_charge || '0'));
});

const isCharging = computed(() => {
  return props.batteryData?.current > 0;
});
</script>

<style lang="scss" scoped>

</style>