export const env = {
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  API_TIMEOUT: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,
  ENABLE_ANALYTICS: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  ENVIRONMENT: import.meta.env.MODE || 'development',
  VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
} as const;

export const isDevelopment = env.ENVIRONMENT === 'development';
export const isProduction = env.ENVIRONMENT === 'production';
