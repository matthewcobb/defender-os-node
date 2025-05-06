<template>
  <div>
    <div>
      <div class="btn" :class="{ 'btn-primary': isConnected, 'btn-danger': !isConnected }" v-if="isConnected">
        Connected
      </div>
    </div>

    <hr>

    <div>
      <dl>
        <dt>Reconnection attempts:</dt>
        <dd>{{ reconnectionAttempts }}</dd>

        <dt>Last activity:</dt>
        <dd>{{ lastActivity }}</dd>

        <dt>Events received:</dt>
        <dd>{{ eventsReceived }}</dd>
      </dl>
    </div>

    <hr>

    <div>
      <button class="btn btn-full" @click="sendPing">Send Ping</button>
      <button class="btn btn-danger btn-full" @click="forceReconnect">Force Reconnect</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import {
  socketEvents,
  sendPing,
  isConnected as getSocketConnected,
  forceReconnect as socketForceReconnect,
  getReconnectionAttempts
} from '../../features/system/services/socketio';

// Connection state
const isConnected = ref(getSocketConnected());
const connectionTime = ref<Date | null>(null);
const reconnectionAttempts = ref(getReconnectionAttempts());
const lastActivity = ref('Never');
const eventsReceived = ref(0);

// Actions
const forceReconnect = () => {
  if (confirm('Are you sure you want to force a reconnection?')) {
    socketForceReconnect();
  }
};

// Update connection state on socket events
const handleConnectionChange = (connected: boolean) => {
  isConnected.value = connected;
  reconnectionAttempts.value = getReconnectionAttempts();

  if (connected) {
    connectionTime.value = new Date();
    lastActivity.value = new Date().toLocaleTimeString();
  }
};

// Track events received
const handleAnyEvent = () => {
  eventsReceived.value++;
  lastActivity.value = new Date().toLocaleTimeString();
};

// Set up event listeners
onMounted(() => {
  // Initialize connection time if already connected
  if (isConnected.value) {
    connectionTime.value = new Date();
  }

  // Listen for socket events
  socketEvents.on('connected', handleConnectionChange);

  // Listen for all events to track activity
  socketEvents.on('*', handleAnyEvent);
});

onUnmounted(() => {
  // Clean up event listeners
  socketEvents.off('connected', handleConnectionChange);
  socketEvents.off('*', handleAnyEvent);
});
</script>