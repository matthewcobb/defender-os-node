<template>
  <div class="level-container" :class="{ 'charging': charging }">
    <div
      class="level"
      :class="[type, getColorClass, { charging: charging }]"
      :style="{
        width: percentage + '%',
        '--final-width': percentage + '%'
      }"
    >
      <span class="indicator-text">
        <slot>{{ percentage }}%</slot>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps({
  percentage: {
    type: Number,
    required: true,
    default: 0
  },
  type: {
    type: String,
    default: 'leisure',
    validator: (value: string) => ['leisure', 'solar'].includes(value)
  },
  charging: {
    type: Boolean,
    default: false
  }
});

const getColorClass = computed(() => {
  if (props.type === 'leisure') {
    // Battery level colors
    if (props.percentage <= 10) return 'critical';
    if (props.percentage <= 50) return 'warning';
    if (props.percentage <= 70) return 'good';
    return 'excellent';
  } else {
    // Solar panel colors - blue to green based on performance
    if (props.percentage <= 25) return 'critical';
    if (props.percentage <= 50) return 'warning';
    if (props.percentage <= 75) return 'good';
    return 'excellent';
  }
});
</script>

<style lang="scss" scoped>
.level-container {
  outline: 2px solid var(--panel-bg);
  background: var(--panel-bg);
  border-radius: 1rem;
  width: 100%;
  margin-bottom: 0.75rem;
  position: relative;
  height: 3rem;
  &.charging {
    background-image: linear-gradient(
      -45deg,
      var(--panel-bg) 25%,
      transparent 25%,
      transparent 50%,
      var(--panel-bg) 50%,
      var(--panel-bg) 75%,
      transparent 75%,
      transparent
    );
    background-size: 30px 30px;
    animation:
      move 1.5s linear infinite;
  }
}

.level {
  height: 100%;
  border-radius: 10px;
  transition: width 0.8s ease-out;
  text-align: center;
  font-size: 1.5rem;
  font-weight: 500;
  box-sizing: border-box;
  border-radius: 1rem;
  overflow: visible;
  animation: fill 1.5s ease-in-out;
  animation-fill-mode: forwards;
  min-width: 100px;
  position: relative;
  display: flex;
  align-items: center;
  &.charging {
    background: linear-gradient(90deg, #4CAF50, #4caf91);
    outline: 2px solid var(--primary);
    animation:
      fill 1.5s ease-out,
      pulse 3s infinite ease-in-out;
  }
}

.indicator-text {
  display: inline-block;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  animation: fadeIn 0.8s ease-in;
  animation-delay: 0.4s;
  animation-fill-mode: both;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 2px 0 var(--primary);
  }
  30% {
    box-shadow: 0 0 1rem 0 var(--primary);
  }
  60% {
    box-shadow: 0 0 2px 0 var(--primary);
  }
  100% {
    box-shadow: 0 0 2px 0 var(--primary);
  }
}

@keyframes fadeIn {
  0% {
    opacity: 0;
  }
  100% {
    opacity: 1;
  }
}

@keyframes fill {
  0% {
    width: 60px;
    opacity: 0.7;
  }
  100% {
    width: var(--final-width);
    opacity: 1;
  }
}

// Battery level gradients
.critical {
  background: linear-gradient(90deg, #d3582f, #d3732f);
}

.warning {
  background: linear-gradient(90deg, #d3732f, #f4bf20);
}

.good {
  background: linear-gradient(90deg, #4CAF50, #4caf91);
}

.excellent {
  background: linear-gradient(90deg, #4caf91, #28aac2);
}

@keyframes move {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 30px 0;
  }
}
</style>