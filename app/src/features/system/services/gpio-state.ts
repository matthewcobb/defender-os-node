/**
 * This file exports the shared state variables from the GPIO service
 * so components can use them without reinitializing the service.
 */
import { ref } from 'vue';

// Shared state for GPIO
export const isReversing = ref(false);
export const isConnected = ref(false);