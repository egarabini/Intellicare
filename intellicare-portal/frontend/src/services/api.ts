import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { refreshToken } from './authService';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8004/api/v1',
});

// Request interceptor: add auth token + preemptive refresh
api.interceptors.request.use(async (config) => {
  const { accessToken, expiry } = useAuthStore.getState();

  // Proactive refresh: if token expires in less than 5 minutes (300 seconds)
  if (accessToken && expiry) {
    const timeLeft = expiry - Date.now();
    if (timeLeft < 300000) { // 5 minutes in ms
      await refreshToken();
    }
  }

  // Grab latest token (could be the newly refreshed one)
  const currentToken = useAuthStore.getState().accessToken;
  if (currentToken && config.headers) {
    config.headers.Authorization = `Bearer ${currentToken}`;
  }

  return config;
});

// Response interceptor: graceful 401 retry 
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Prevent infinite loops on /token endpoint if refresh also returns 401
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshed = await refreshToken();
      if (refreshed) {
        const token = useAuthStore.getState().accessToken;
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return api(originalRequest);
      }

      // Refresh failed, clear session and send to login
      useAuthStore.getState().clear();
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

export default api;
