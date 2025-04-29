import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { socketEvents, initSocketIO } from '../features/system/services/socketio';

// Define interfaces for Renogy data
export interface SolarData {
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

export interface BatteryData {
  function?: string;
  cell_count?: number;
  sensor_count?: number;
  current?: number;
  voltage?: number;
  time_remaining_to_charge?: string;
  time_remaining_to_empty?: string;
  pv_power?: number;
  load_power?: number;
  remaining_charge?: number;
  capacity?: number;
  model?: string;
  device_id?: number;
  [key: string]: any; // For dynamic properties like cell_voltage_0, temperature_0, etc.
}

export const useRenogyStore = defineStore('renogy', () => {
  // State
  const solarData = ref<SolarData>({});
  const batteryData = ref<BatteryData>({});
  const error = ref<string>('Connecting...');
  const isInitialized = ref(false);
  const isConnected = ref(false);

  // Getters
  const isFullyCharged = computed(() => {
    return (batteryData.value?.remaining_charge ?? 0) > 99.5;
  });

  const batteryPercentage = computed(() => {
    return Math.round(parseFloat(String(batteryData.value?.remaining_charge ?? '0')));
  });

  const isCharging = computed(() => {
    return (batteryData.value?.current ?? 0) > 0;
  });

  const cellCount = computed(() => {
    return batteryData.value?.cell_count ?? 0;
  });

  const sensorCount = computed(() => {
    return batteryData.value?.sensor_count ?? 0;
  });

  const solarPowerPercentage = computed(() => {
    const currentPower = solarData.value?.pv_power || 0;
    const maxPower = solarData.value?.max_charging_power_today || 200;
    const percentage = (currentPower / maxPower) * 100;
    return Math.min(percentage, 100); // Cap at 100%
  });

  // Helper functions
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

  // Socket.IO event handlers
  const handleConnectionChange = (connected: boolean) => {
    isConnected.value = connected;
    if (!connected) {
      error.value = 'Disconnected from server';
    } else {
      error.value = '';
    }
  };

  const handleRenogyData = (data: any) => {
    if (data && typeof data === 'object') {
      if (data.solar) {
        solarData.value = data.solar;
      }
      if (data.battery) {
        batteryData.value = data.battery;
      }
      error.value = '';
    }
  };

  // Initialize Socket.IO and set up event listeners
  const init = () => {
    if (isInitialized.value) return;

    // Initialize the Socket.IO connection
    initSocketIO();

    // Set up event listeners
    socketEvents.on('connected', handleConnectionChange);
    socketEvents.on('renogy:data_update', handleRenogyData);
    socketEvents.on('renogy:initial_state', handleRenogyData);
    isInitialized.value = true;
  };

  // Cleanup when component unmounts
  const cleanup = () => {
    socketEvents.off('connected', handleConnectionChange);
    socketEvents.off('renogy:data_update', handleRenogyData);
    socketEvents.off('renogy:initial_state', handleRenogyData);
  };

  return {
    // State
    solarData,
    batteryData,
    error,
    isConnected,

    // Getters
    isFullyCharged,
    batteryPercentage,
    isCharging,
    cellCount,
    sensorCount,
    solarPowerPercentage,

    // Helper functions
    formatChargingStatus,
    formatTotalPower,

    // Socket.IO methods
    init,
    cleanup
  };
});