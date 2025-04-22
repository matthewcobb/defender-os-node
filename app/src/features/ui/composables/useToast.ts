import { ref, readonly } from 'vue';

interface ToastState {
  show: boolean;
  text: string;
  type: 'success' | 'error';
  duration: number;
}

// Create a shared state that persists between component instances
const state = ref<ToastState>({
  show: false,
  text: '',
  type: 'success',
  duration: 3000
});

export function useToast() {
  // Method to show a toast notification
  const showToast = (text: string, options?: Partial<Omit<ToastState, 'show' | 'text'>>) => {
    state.value = {
      show: true,
      text,
      type: options?.type || 'success',
      duration: options?.duration || 3000
    };
  };

  // Method to hide the toast
  const hideToast = () => {
    state.value.show = false;
  };

  // Convenience methods for specific types
  const success = (text: string, duration?: number) => {
    showToast(text, { type: 'success', duration });
  };

  const error = (text: string, duration?: number) => {
    showToast(text, { type: 'error', duration });
  };

  // Return read-only state and methods
  return {
    state: readonly(state),
    showToast,
    hideToast,
    success,
    error
  };
}