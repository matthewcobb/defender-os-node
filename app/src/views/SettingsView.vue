<template>
  <div class="settings-view">
    <h1>Settings</h1>

    <div class="settings-section">
      <h2>Display Settings</h2>

      <div class="setting-item">
        <span class="setting-label">Theme</span>
        <select class="setting-control">
          <option value="dark">Dark</option>
          <option value="light">Light</option>
          <option value="auto">System Default</option>
        </select>
      </div>

      <div class="setting-item">
        <span class="setting-label">Display Brightness</span>
        <input type="range" min="0" max="100" value="80" class="setting-control slider" />
      </div>
    </div>

    <div class="settings-section">
      <h2>System Settings</h2>

      <div class="setting-item">
        <span class="setting-label">Auto-start on Boot</span>
        <label class="toggle">
          <input type="checkbox" checked />
          <span class="toggle-slider"></span>
        </label>
      </div>

      <div class="setting-item">
        <span class="setting-label">Update Frequency</span>
        <select class="setting-control">
          <option value="5">Every 5 seconds</option>
          <option value="30">Every 30 seconds</option>
          <option value="60">Every minute</option>
          <option value="300">Every 5 minutes</option>
        </select>
      </div>
    </div>

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
import { ref } from 'vue';
import { apiService } from '../services/api';

const isUpdating = ref(false);
const updateMessage = ref('');
const updateError = ref(false);
const isClosingKiosk = ref(false);
const kioskMessage = ref('');
const kioskError = ref(false);

const updateSystem = async () => {
  if (isUpdating.value) return;

  try {
    isUpdating.value = true;
    updateMessage.value = '';
    updateError.value = false;

    const response = await apiService.updateSystem();

    if (response.status === 'success') {
      updateMessage.value = response.message || 'Update completed successfully.';
    } else {
      updateError.value = true;
      updateMessage.value = response.message || 'Update failed. Please check logs.';
    }
  } catch (error) {
    updateError.value = true;
    updateMessage.value = 'Failed to update the system. Please try again.';
    console.error('Update error:', error);
  } finally {
    // Reset updating status after 10 seconds to allow button re-use
    setTimeout(() => {
      isUpdating.value = false;
    }, 10000);
  }
};

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