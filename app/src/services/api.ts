import axios from 'axios';

const API_URL = 'http://0.0.0.0:5000';

// Create an axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// API methods for each endpoint
export const apiService = {
  /**
   * Get CPU temperature from the server
   */
  getCpuTemp: async () => {
    try {
      const response = await apiClient.get('/cpu_temp');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Trigger system update via fetch.sh
   */
  updateSystem: async () => {
    try {
      const response = await apiClient.post('/update_system');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get the current system update status
   */
  getUpdateStatus: async () => {
    try {
      const response = await apiClient.get('/update_status');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Close Chrome kiosk browser
   */
  closeKiosk: async () => {
    try {
      const response = await apiClient.post('/close_kiosk');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Add more API methods here as needed
};