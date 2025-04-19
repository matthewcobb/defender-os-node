<template>
  <div v-if="show" class="message-toast" :class="type">
    {{ text }}
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

interface Props {
  text?: string;
  type?: 'success' | 'error';
  duration?: number;
  show?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  text: '',
  type: 'success',
  duration: 3000,
  show: false,
});

const emit = defineEmits(['update:show', 'closed']);

// Local ref to handle animation before actual hiding
const show = ref(props.show);

// Watch for show prop changes
watch(() => props.show, (newValue) => {
  show.value = newValue;

  if (newValue && props.duration > 0) {
    setTimeout(() => {
      show.value = false;
      emit('update:show', false);
      emit('closed');
    }, props.duration);
  }
});
</script>

<style lang="scss" scoped>
.message-toast {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  color: white;
  font-weight: 500;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 100;
  animation: fade-in 0.3s ease-in-out;

  &.success {
    background-color: var(--charging-base);
  }

  &.error {
    background-color: #e53935;
  }
}

@keyframes fade-in {
  from { opacity: 0; transform: translate(-50%, 1rem); }
  to { opacity: 1; transform: translate(-50%, 0); }
}
</style>