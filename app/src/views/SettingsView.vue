<template>
  <div class="settings-view">
    <h1>Settings</h1>

    <div class="settings-section">
      <h2>System Maintenance</h2>

      <div class="setting-item">
        <span class="setting-label">Update System</span>
        <button class="action-button" @click="updateSystem" :disabled="isUpdating">
          {{ isUpdating ? 'Updating...' : 'Update Now' }}
        </button>
      </div>
      <div v-if="updateMessage" class="update-message" :class="{ 'update-error': updateError }">
        {{ updateMessage }}
      </div>

      <div v-if="updateProgress && updateProgress.steps && updateProgress.steps.length > 0" class="update-progress">
        <div
          v-for="(step, index) in updateProgress.steps"
          :key="step.name"
          class="progress-step"
          :class="{
            'step-pending': step.status === 'pending',
            'step-in-progress': step.status === 'in_progress',
            'step-complete': step.status === 'complete',
            'step-failed': step.status === 'failed'
          }"
        >
          <div class="step-indicator">
            <span v-if="step.status === 'complete'">✓</span>
            <span v-else-if="step.status === 'failed'">✗</span>
            <span v-else-if="step.status === 'in_progress'">●</span>
            <span v-else>○</span>
          </div>
          <div class="step-details">
            <div class="step-name">{{ step.message || `Step ${index + 1}` }}</div>
            <div v-if="step.status === 'failed' && step.error" class="step-error">
              {{ step.error }}
            </div>
          </div>
        </div>
      </div>

      <div class="setting-item">
        <span class="setting-label">Close Browser Kiosk</span>
        <button class="action-button danger" @click="closeKiosk" :disabled="isClosingKiosk">
          {{ isClosingKiosk ? 'Closing...' : 'Close Kiosk' }}
        </button>
      </div>
      <div v-if="kioskMessage" class="update-message" :class="{ 'update-error': kioskError }">
        {{ kioskMessage }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue';
import { apiService } from '../services/api';
import { createPeriodicFetcher } from '../features/system/composables/useApi';

const isUpdating = ref(false);
const updateMessage = ref('');
const updateError = ref(false);
const isClosingKiosk = ref(false);
const kioskMessage = ref('');
const kioskError = ref(false);

// For tracking update status
const updateProgress = ref<any>(null);
let stopUpdateStatusPolling: (() => void) | null = null;

const checkUpdateStatus = async () => {
  try {
    const status = await apiService.getUpdateStatus();
    updateProgress.value = status;

    // Update message based on current step
    if (status.overall_status === 'in_progress' && status.current_step >= 0 && status.steps.length > 0) {
      const currentStep = status.steps[status.current_step];
      updateMessage.value = `${currentStep.message} (Step ${status.current_step + 1}/${status.steps.length})`;
    } else if (status.overall_status === 'complete') {
      updateMessage.value = 'Update completed successfully! The page will reload shortly...';

      // Stop polling
      if (stopUpdateStatusPolling) {
        stopUpdateStatusPolling();
        stopUpdateStatusPolling = null;
      }

      // Set a timer to reload the page
      setTimeout(() => {
        window.location.reload();
      }, 5000);

      // Reset status
      isUpdating.value = false;
    } else if (status.overall_status === 'failed') {
      updateError.value = true;
      updateMessage.value = `Update failed: ${status.error || 'Unknown error'}`;

      // Stop polling
      if (stopUpdateStatusPolling) {
        stopUpdateStatusPolling();
        stopUpdateStatusPolling = null;
      }

      // Reset status
      isUpdating.value = false;
    }
  } catch (error) {
    console.error('Error checking update status:', error);
  }
};

// Create periodic fetcher for update status
const startUpdateStatusPolling = createPeriodicFetcher(checkUpdateStatus, 2000);

const updateSystem = async () => {
  if (isUpdating.value) return;

  try {
    isUpdating.value = true;
    updateMessage.value = '';
    updateError.value = false;
    updateProgress.value = null;

    const response = await apiService.updateSystem();

    if (response.status === 'initiated') {
      updateMessage.value = 'Update started. Monitoring progress...';

      // Start polling for update status
      stopUpdateStatusPolling = startUpdateStatusPolling();
    } else {
      updateError.value = true;
      updateMessage.value = response.message || 'Failed to start update process.';
    }
  } catch (error) {
    updateError.value = true;
    updateMessage.value = 'Failed to update the system. Please try again.';
    console.error('Update error:', error);
    isUpdating.value = false;
  }
};

// Clean up interval on component unmount
onUnmounted(() => {
  if (stopUpdateStatusPolling) {
    stopUpdateStatusPolling();
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
  } catch (error) {
    kioskError.value = true;
    kioskMessage.value = 'Failed to close the kiosk. Please try again.';
    console.error('Kiosk close error:', error);
  } finally {
    // Reset closing status after 10 seconds to allow button re-use
    setTimeout(() => {
      isClosingKiosk.value = false;
    }, 10000);
  }
};
</script>

<style lang="scss" scoped>
.settings-view {
}

h1 {
  margin-bottom: 2rem;
  color: #4CAF50;
}

h2 {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: #ddd;
}

.settings-section {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

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

.setting-label {
  font-weight: 500;
}

.setting-control {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  padding: 0.5rem;
  color: white;
}

.slider {
  width: 150px;
  -webkit-appearance: none;
  height: 6px;
  border-radius: 3px;
  background: #444;

  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: #4CAF50;
    cursor: pointer;
  }
}

.toggle {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;

  input {
    opacity: 0;
    width: 0;
    height: 0;

    &:checked + .toggle-slider {
      background-color: #4CAF50;

      &:before {
        transform: translateX(24px);
      }
    }
  }
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #444;
  border-radius: 24px;
  transition: 0.4s;

  &:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    border-radius: 50%;
    transition: 0.4s;
  }
}

.action-button {
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-weight: 500;

  &:hover {
    background-color: #3e8e41;
  }

  &:disabled {
    background-color: #888;
    cursor: not-allowed;
  }
}

.update-message {
  margin-top: 0.5rem;
  padding: 0.5rem;
  border-radius: 4px;
  background-color: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
  font-size: 0.9rem;
}

.update-error {
  background-color: rgba(244, 67, 54, 0.1);
  color: #f44336;
}

.update-progress {
  margin-top: 1rem;
  margin-bottom: 1rem;
  padding: 0.5rem;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.2);
}

.progress-step {
  display: flex;
  align-items: flex-start;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  &:last-child {
    border-bottom: none;
  }
}

.step-indicator {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 20px;
  height: 20px;
  margin-right: 10px;
  border-radius: 50%;
  font-size: 12px;
}

.step-details {
  flex: 1;
}

.step-name {
  font-size: 0.9rem;
}

.step-error {
  font-size: 0.8rem;
  color: #f44336;
  margin-top: 0.25rem;
}

.step-pending {
  opacity: 0.5;

  .step-indicator {
    color: #aaa;
  }
}

.step-in-progress {
  .step-indicator {
    color: #2196F3;
  }

  .step-name {
    color: #2196F3;
  }
}

.step-complete {
  .step-indicator {
    color: #4CAF50;
  }
}

.step-failed {
  .step-indicator {
    color: #f44336;
  }
}

.danger {
  background-color: #f44336;

  &:hover {
    background-color: #d32f2f;
  }

  &:disabled {
    background-color: #888;
    cursor: not-allowed;
  }
}
</style>