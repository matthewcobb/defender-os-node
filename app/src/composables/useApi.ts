import { ref } from 'vue';
import { apiService } from '../services/api';

/**
 * Composable to fetch CPU temperature
 */
export function useCpuTemp() {
  const temp = ref<string | null>(null);
  const error = ref<string>('');
  const loading = ref<boolean>(false);

  /**
   * Fetch CPU temperature from the API
   */
  const fetchCpuTemp = async () => {
    loading.value = true;
    error.value = '';

    try {
      const data = await apiService.getCpuTemp();

      if (data.error) {
        throw new Error(data.error);
      }

      temp.value = data.temp;
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch CPU temperature';
      temp.value = null;
    } finally {
      loading.value = false;
    }
  };

  return {
    temp,
    error,
    loading,
    fetchCpuTemp
  };
}

/**
 * Factory function to create reusable API data fetchers with interval
 */
export function createPeriodicFetcher(
  fetchFunction: () => Promise<void>,
  intervalMs: number = 10000
) {
  const startFetching = () => {
    // Initial fetch
    fetchFunction();

    // Set up interval
    const intervalId = setInterval(() => {
      fetchFunction();
    }, intervalMs);

    // Return cleanup function
    return () => {
      clearInterval(intervalId);
    };
  };

  return startFetching;
}

/**
 * Add more composables here as needed for other API endpoints
 */