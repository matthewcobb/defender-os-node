import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { socketEvents, initSocketIO } from '../features/system/services/socketio';

// Define interface for Renogy data
export interface RenogyData {
  // Common data
  model?: string;
  device_id?: number;

  // Battery data
  battery_voltage?: number;
  battery_current?: number;
  battery_percentage?: number;
  battery_power?: number;
  remaining_charge?: number;
  capacity?: number;
  time_remaining_to_charge?: string;
  time_remaining_to_empty?: string;

  // Solar data
  controller_temperature?: number;
  pv_current?: number;
  pv_power?: number;
  load_power?: number;
  load_current?: number;
  max_charging_power_today?: number;
  power_generation_today?: number;
  power_generation_total?: number;
  charger_status?: string;

  // Dynamic properties
  cell_count?: number;
  sensor_count?: number;
  [key: string]: any; // For dynamic properties like cell_voltage_0, temperature_0, etc.
}

export const useRenogyStore = defineStore('renogy', () => {
  // State
  const data = ref<RenogyData>({});
  const devicesReady = ref(false);
  const isInitialized = ref(false);
  const isConnected = ref(false);
  const error = ref(null);
  // Getters
  const isFullyCharged = computed(() => {
    return (data.value?.remaining_charge ?? 0) > 99.5;
  });

  const batteryPercentage = computed(() => {
    return Math.round(parseFloat(String(data.value?.battery_percentage ?? '0')));
  });

  const dischargeWatts = computed(() => {
    return Number((data.value?.battery_power ?? 0).toFixed(1));
  });

  const isCharging = computed(() => {
    return (data.value?.battery_status === 'charging');
  });

  const cellCount = computed(() => {
    return data.value?.cell_count ?? 0;
  });

  const sensorCount = computed(() => {
    return data.value?.sensor_count ?? 0;
  });

  const currentPowerOutput = computed(() => {
    return Math.abs((data.value?.load_power ?? 0) - (data.value?.battery_power ?? 0));
  });

  const solarPowerPercentage = computed(() => {
    const currentPower = data.value?.pv_power || 0;
    const maxPower = 200; // Supply on roof
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
      devicesReady.value = false;
    }
  };

  const handleRenogyData = (receivedData: any) => {
    if (receivedData && typeof receivedData === 'object') {
      devicesReady.value = true;
      data.value = receivedData;
    }
  };

  const handleRenogyError = (error: any) => {
    console.error('Renogy error:', error);
    devicesReady.value = false;
    error.value = error;
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
    socketEvents.on('renogy:error', handleRenogyError);
    isInitialized.value = true;
  };

  // Cleanup when component unmounts
  const cleanup = () => {
    socketEvents.off('connected', handleConnectionChange);
    socketEvents.off('renogy:data_update', handleRenogyData);
    socketEvents.off('renogy:initial_state', handleRenogyData);
    socketEvents.off('renogy:error', handleRenogyError);
  };

  return {
    // State
    data,
    error,
    devicesReady,
    isConnected,

    // Getters
    isFullyCharged,
    batteryPercentage,
    dischargeWatts,
    isCharging,
    currentPowerOutput,
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