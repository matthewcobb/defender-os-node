<template>
  <div class="panel solar">
    <div class="panel-header">
      <h2>Charger</h2>
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
          <h4>Current</h4>
          <p class="value">
            <BatteryMedium :size="24" class="icon" />
            {{ renogyStore.data?.pv_current || '0' }}A
          </p>
        </div>
        <div class="stat">
          <h4 class="text-center">+Today</h4>
          <p class="value">
            <Calendar :size="24" class="icon" />
            {{ renogyStore.data?.power_generation_today || '0' }}Wh
          </p>
        </div>
        <div class="stat">
          <h4 class="text-right">Usage</h4>
          <p class="value">
            <Zap :size="24" class="icon" />
            {{ renogyStore.currentPowerOutput || '0' }}W
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Sun, BatteryMedium, Calendar, Zap } from 'lucide-vue-next';
import LevelIndicator from './LevelIndicator.vue';
import { useRenogyStore } from '../stores/renogyStore';

const renogyStore = useRenogyStore();
</script>

<style lang="scss" scoped>
</style>