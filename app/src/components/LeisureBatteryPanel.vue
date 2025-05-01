<template>
  <div class="panel leisure" :class="{ 'charging': renogyStore.isCharging }">
    <div class="panel-header">
      <h2>Battery</h2>
      <BatteryMedium class="leisure" :size="32" />
    </div>
    <div v-if="!renogyStore.devicesReady" class="error-state">
      <p class="small">Connecting...</p>
    </div>
    <div v-else>
      <LevelIndicator
        :percentage="renogyStore.batteryPercentage"
        type="leisure"
        :charging="renogyStore.isCharging"
      >
        {{ renogyStore.batteryPercentage }}%
      </LevelIndicator>
      <div class="grid justify-between">
        <div class="stat">
          <div v-if="renogyStore.isFullyCharged">
            <h4>Battery is full</h4>
            <p class="value">
              <Gauge :size="24" class="icon" />
              --
            </p>
          </div>
          <div v-else-if="renogyStore.isCharging">
            <h4>Time until full</h4>
            <p class="value">
              <Gauge :size="24" class="icon" />
              {{ renogyStore.data?.time_remaining_to_charge || '0' }}
            </p>
          </div>
          <div v-else>
            <h4>Time until empty</h4>
            <p class="value">
              <Gauge :size="24" class="icon" />
              {{ renogyStore.data?.time_remaining_to_empty || '0' }}
            </p>
          </div>
        </div>
        <div class="stat text-right">
          <h4>Current</h4>
          <p class="value">
            {{ renogyStore.data?.battery_power || '0' }}W
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { BatteryMedium, Gauge } from 'lucide-vue-next';
import LevelIndicator from './LevelIndicator.vue';
import { useRenogyStore } from '../stores/renogyStore';

const renogyStore = useRenogyStore();
</script>

<style lang="scss" scoped>

</style>