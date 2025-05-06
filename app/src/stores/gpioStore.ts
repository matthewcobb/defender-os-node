import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { socketEvents } from '../features/system/services/socketio';

export const useGpioStore = defineStore('gpio', () => {
  // State
  const isReversing = ref(false);
  const isConnected = ref(false);
  const isInitialized = ref(false);

  // Router reference for navigation
  let router: ReturnType<typeof useRouter> | null = null;

  // Handle reverse state change events from Socket.IO
  const handleReverseStateChange = (data: any) => {
    if (data && typeof data === 'object') {
      const newReversingState = data.is_reversing ?? false;

      // Update state
      isReversing.value = newReversingState;

      // Handle navigation based on reversing state
      if (newReversingState) {
        // If we start reversing and we have a router, navigate to the reverse camera view
        if (router && router.currentRoute.value.name !== 'reverse') {
          // Add query parameter to indicate this was triggered by sensor
          router.push({
            path: '/reverse',
            query: { sensor: 'true', fullscreen: 'true' }
          });
        }
      }
    }
  };

  // Initialize the store and set up event listeners
  const init = (routerInstance?: ReturnType<typeof useRouter>) => {
    if (isInitialized.value) return;

    // Store router reference if provided
    if (routerInstance) {
      router = routerInstance;
    }

    // Set up event listeners for GPIO-related events
    socketEvents.on('gpio:reverse_state_change', handleReverseStateChange);
    socketEvents.on('gpio:initial_state', handleReverseStateChange);

    // Update connection state
    socketEvents.on('connected', (connected) => {
      isConnected.value = connected;
    });

    isInitialized.value = true;
  };

  // Clean up event listeners
  const cleanup = () => {
    socketEvents.off('gpio:reverse_state_change', handleReverseStateChange);
    socketEvents.off('gpio:initial_state', handleReverseStateChange);
    socketEvents.off('connected');
    isInitialized.value = false;
  };

  return {
    // State
    isReversing,
    isConnected,
    isInitialized,

    // Actions
    init,
    cleanup
  };
});