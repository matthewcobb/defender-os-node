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
  </div>
</template>

<script setup lang="ts">
// Settings view component
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
</style>