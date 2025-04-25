import { ref, onMounted, onUnmounted } from 'vue';
import { socketEvents, initSocketIO, sendMessage } from '../services/socketio';

export interface UpdateStatus {
  overall_status: 'not_started' | 'in_progress' | 'complete' | 'failed';
  logs: string[];
  current_step: {
    name: string;
    status: string;
    message: string;
  } | null;
  error: string | null;
}

export function useSystemUpdates() {
  const updateStatus = ref<UpdateStatus>({
    overall_status: 'not_started',
    logs: [],
    current_step: null,
    error: null
  });

  const isUpdating = ref(false);
  const updateComplete = ref(false);
  const updateFailed = ref(false);

  // Handle Socket.IO updates
  const handleUpdateStatus = (data: UpdateStatus) => {
    updateStatus.value = data;
    isUpdating.value = data.overall_status === 'in_progress';
    updateComplete.value = data.overall_status === 'complete';
    updateFailed.value = data.overall_status === 'failed';
  };

  // Start a system update via websocket
  const startUpdate = () => {
    sendMessage('system_request_update');
    // Initial state will be sent over Socket.IO
  };

  onMounted(() => {
    // Make sure Socket.IO is initialized
    initSocketIO();

    // Subscribe to Socket.IO events
    socketEvents.on('system:update_status', handleUpdateStatus);
    socketEvents.on('system:initial_state', handleUpdateStatus);
  });

  onUnmounted(() => {
    // Clean up Socket.IO listeners
    socketEvents.off('system:update_status', handleUpdateStatus);
    socketEvents.off('system:initial_state', handleUpdateStatus);
  });

  return {
    updateStatus,
    isUpdating,
    updateComplete,
    updateFailed,
    startUpdate
  };
}