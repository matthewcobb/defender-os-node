<template>
  <div class="panel solar">
    <div class="panel-header">
      <h2>Solar</h2>
      <Sun class="solar" :size="32" />
    </div>
    <div v-if="!renogyStore.devicesReady" class="error-state">
      <p class="small">Connecting...</p>
    </div>
    <div v-else>
      <LevelIndicator :percentage="renogyStore.solarPowerPercentage" type="solar">
        {{ renogyStore.data?.pv_power || '0' }}W
      </LevelIndicator>
      <div class="grid justify-between">
        <div class="stat">
          <h4>Voltage</h4>
          <p class="value">
            <BatteryMedium :size="24" class="icon" />
            {{ renogyStore.data?.pv_voltage || '0' }}V
          </p>
        </div>
        <div class="stat">
          <h4 class="text-center">Load</h4>
          <p class="value">
            <ArrowRight :size="24" class="icon" />
            {{ renogyStore.data?.load_power || '0' }}A
          </p>
        </div>
        <div class="stat">
          <h4 class="text-right">Today</h4>
          <p class="value">
            <Calendar :size="24" class="icon" />
            {{ renogyStore.data?.power_generation_today || '0' }}Wh
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Sun, BatteryMedium, ArrowRight, Calendar } from 'lucide-vue-next';
import LevelIndicator from './LevelIndicator.vue';
import { useRenogyStore } from '../stores/renogyStore';

const renogyStore = useRenogyStore();
</script>

<style lang="scss" scoped>
</style>