import axios, { InternalAxiosRequestConfig } from 'axios'

// VITE_API_BASE_URL pode ser definido em .env.local para desenvolvimento
// Default: path relativo /admin (funciona em qualquer porta, sem duplo-prefixo)
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/admin',
  timeout: 30_000,
})

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = sessionStorage.getItem('oidc.access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default apiClient
