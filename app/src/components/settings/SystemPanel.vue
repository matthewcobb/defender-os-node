<template>
  <div class="panel">
    <h2>System</h2>

    <div class="setting-item">
      <h4>Update System</h4>
      <button class="btn btn-primary" @click="startUpdate" :disabled="isUpdating">
        {{ isUpdating ? 'Updating...' : 'Update Now' }}
      </button>
    </div>
    <div v-if="updateMessage" class="update-message" :class="{ 'update-error': updateError }">
      {{ updateMessage }}
    </div>

    <!-- Display current step if available -->
    <div v-if="updateStatus.current_step" class="current-step">
      <div class="step-indicator">
        <span class="step-icon">🔄</span>
      </div>
      <div class="step-details">
        <div class="step-name">{{ formatStepName(updateStatus.current_step.name) }}</div>
        <div class="step-message">{{ updateStatus.current_step.message }}</div>
      </div>
    </div>

    <!-- Display logs from the update process -->
    <div v-if="updateStatus.logs && updateStatus.logs.length > 0" class="update-logs">
      <h4>Update Log</h4>
      <div class="logs-container">
        <div v-for="(log, index) in updateStatus.logs" :key="index" class="log-line">
          {{ log }}
        </div>
      </div>
    </div>

    <div class="setting-item">
      <h4>Close</h4>
      <button class="btn btn-danger" @click="closeKiosk" :disabled="isClosingKiosk">
        {{ isClosingKiosk ? 'Closing...' : 'Close Kiosk' }}
      </button>
    </div>
    <div v-if="kioskMessage" class="update-message" :class="{ 'update-error': kioskError }">
      {{ kioskMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useToast } from '../../features';
import { apiService } from '../../features/system/services/api';
import { useSystemUpdates } from '../../features/system/composables/useSystemUpdates';

const { isUpdating, updateStatus, updateComplete, updateFailed, startUpdate } = useSystemUpdates();

const isClosingKiosk = ref(false);
const updateMessage = ref('');
const updateError = ref(false);
const kioskMessage = ref('');
const kioskError = ref(false);

// Use the global toast system
const { success, error } = useToast();

// Format step name to be more readable
const formatStepName = (name: string) => {
  if (!name) return '';

  // Convert snake_case to Title Case
  return name.split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Watch for changes in update status
watch([updateStatus, updateComplete, updateFailed], ([status, complete, failed]) => {
  if (status.overall_status === 'in_progress') {
    if (status.current_step) {
      updateMessage.value = `Update in progress: ${formatStepName(status.current_step.name)}`;
    } else {
      updateMessage.value = 'Update in progress...';
    }
  } else if (complete) {
    updateMessage.value = 'Update completed successfully! The page will reload shortly...';
    success('Update completed successfully');

    // Set a timer to reload the page
    setTimeout(() => {
      window.location.reload();
    }, 5000);
  } else if (failed) {
    updateError.value = true;
    updateMessage.value = `Update failed: ${status.error || 'Unknown error'}`;
    error('Update failed');
  }
});

const closeKiosk = async () => {
  if (isClosingKiosk.value) return;

  try {
    isClosingKiosk.value = true;
    kioskMessage.value = '';
    kioskError.value = false;

    await apiService.closeKiosk();

    kioskMessage.value = 'Kiosk closed successfully.';
    success('Kiosk closed successfully');
  } catch (err) {
    kioskError.value = true;
    kioskMessage.value = 'Failed to close the kiosk. Please try again.';
    error('Failed to close kiosk');
    console.error('Kiosk close error:', err);
  } finally {
    // Reset closing status after 10 seconds to allow button re-use
    setTimeout(() => {
      isClosingKiosk.value = false;
    }, 10000);
  }
};
</script>

<style lang="scss" scoped>
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  &:last-child {
    border-bottom: none;
  }
}

.update-message {
  margin-top: 0.5rem;
  padding: 0.5rem;
  border-radius: 4px;
  background-color: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
  font-size: 0.9rem;

  &.update-error {
    background-color: rgba(244, 67, 54, 0.1);
    color: var(--danger);
  }
}

.current-step {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  display: flex;
  align-items: flex-start;
}

.step-indicator {
  margin-right: 0.75rem;
  font-size: 1.2rem;
}

.step-details {
  flex-grow: 1;
}

.step-name {
  font-weight: bold;
  margin-bottom: 0.25rem;
}

.update-logs {
  margin-top: 1rem;
  margin-bottom: 1rem;
}

.logs-container {
  max-height: 300px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 0.85rem;
  background-color: rgba(0, 0, 0, 0.5);
  padding: 0.5rem;
  border-radius: 4px;
  margin-top: 0.5rem;
}

.log-line {
  padding: 0.15rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  white-space: pre-wrap;

  &:last-child {
    border-bottom: none;
  }
}
</style>