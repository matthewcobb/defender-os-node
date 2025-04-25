<template>
  <div class="system-update-status">
    <div class="status-header">
      <h3>System Update Status</h3>
      <div class="status-badge" :class="statusClass">
        {{ statusLabel }}
      </div>
    </div>

    <div v-if="!isUpdating && !updateComplete && !updateFailed" class="update-actions">
      <button class="update-button" @click="startUpdate">
        Start Update
      </button>
    </div>

    <div v-if="updateStatus.current_step" class="current-step">
      <h4>Current Step: {{ updateStatus.current_step.name }}</h4>
      <p>{{ updateStatus.current_step.message }}</p>
    </div>

    <div v-if="updateFailed && updateStatus.error" class="update-error">
      <h4>Error</h4>
      <p>{{ updateStatus.error }}</p>
    </div>

    <div v-if="isUpdating || updateComplete || updateFailed" class="update-logs">
      <h4>Update Logs</h4>
      <div class="logs-container" ref="logsContainer">
        <div v-for="(log, index) in updateStatus.logs" :key="index" class="log-entry">
          {{ log }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useSystemUpdates } from '../features/system/composables/useSystemUpdates';

const { updateStatus, isUpdating, updateComplete, updateFailed, startUpdate } = useSystemUpdates();

const logsContainer = ref<HTMLDivElement | null>(null);

// Scroll to bottom when new logs are added
watch(
  () => updateStatus.value.logs.length,
  () => {
    setTimeout(() => {
      if (logsContainer.value) {
        logsContainer.value.scrollTop = logsContainer.value.scrollHeight;
      }
    }, 0);
  }
);

// Compute status label
const statusLabel = computed(() => {
  if (updateStatus.value.overall_status === 'not_started') return 'Not Started';
  if (updateStatus.value.overall_status === 'in_progress') return 'In Progress';
  if (updateStatus.value.overall_status === 'complete') return 'Complete';
  if (updateStatus.value.overall_status === 'failed') return 'Failed';
  return 'Unknown';
});

// Compute CSS class for status badge
const statusClass = computed(() => {
  if (updateStatus.value.overall_status === 'not_started') return 'status-not-started';
  if (updateStatus.value.overall_status === 'in_progress') return 'status-in-progress';
  if (updateStatus.value.overall_status === 'complete') return 'status-complete';
  if (updateStatus.value.overall_status === 'failed') return 'status-failed';
  return '';
});
</script>

<style lang="scss" scoped>
.system-update-status {
  padding: 1rem;
  border-radius: 0.5rem;
  background-color: var(--color-background-soft);
  max-width: 800px;
  margin: 0 auto;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;

  h3 {
    margin: 0;
  }
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-not-started {
  background-color: var(--color-gray-200);
  color: var(--color-gray-700);
}

.status-in-progress {
  background-color: var(--color-blue-100);
  color: var(--color-blue-700);
}

.status-complete {
  background-color: var(--color-green-100);
  color: var(--color-green-700);
}

.status-failed {
  background-color: var(--color-red-100);
  color: var(--color-red-700);
}

.update-actions {
  margin-bottom: 1rem;
}

.update-button {
  padding: 0.5rem 1rem;
  background-color: var(--color-primary);
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-weight: 500;

  &:hover {
    background-color: var(--color-primary-dark);
  }
}

.current-step {
  margin-bottom: 1rem;
  padding: 0.5rem;
  background-color: var(--color-blue-50);
  border-radius: 0.25rem;

  h4 {
    margin-top: 0;
    margin-bottom: 0.5rem;
  }

  p {
    margin: 0;
  }
}

.update-error {
  margin-bottom: 1rem;
  padding: 0.5rem;
  background-color: var(--color-red-50);
  border-radius: 0.25rem;
  border-left: 4px solid var(--color-red-500);

  h4 {
    margin-top: 0;
    margin-bottom: 0.5rem;
    color: var(--color-red-700);
  }

  p {
    margin: 0;
    color: var(--color-red-800);
  }
}

.update-logs {
  h4 {
    margin-top: 0;
    margin-bottom: 0.5rem;
  }
}

.logs-container {
  max-height: 300px;
  overflow-y: auto;
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  padding: 0.5rem;
  font-family: monospace;
  font-size: 0.875rem;
}

.log-entry {
  white-space: pre-wrap;
  line-height: 1.4;
  margin-bottom: 0.25rem;

  &:last-child {
    margin-bottom: 0;
  }
}
</style>