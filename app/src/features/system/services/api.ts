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
   * Remove the splash screen displayed during boot
   */
  removeSplashScreen: async () => {
    try {
      const response = await apiClient.post('/remove_splash');
      console.log('Splash screen removal result:', response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to remove splash screen:', error);
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

  /**
   * Scan for available WiFi networks
   */
  scanWifiNetworks: async () => {
    try {
      const response = await apiClient.post('/wifi/scan');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Connect to a WiFi network
   */
  connectToWifi: async (ssid: string, password: string = '') => {
    try {
      const response = await apiClient.post('/wifi/connect', { ssid, password });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Disconnect from current WiFi network
   */
  disconnectWifi: async () => {
    try {
      const response = await apiClient.post('/wifi/disconnect');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Add more API methods here as needed
};