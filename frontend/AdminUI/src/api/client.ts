import axios, { InternalAxiosRequestConfig } from 'axios'
import { getToken } from '../auth/tokenRef'

// Path relativo — funciona em qualquer porta, sem duplo prefixo.
// Em dev com npm run dev, definir VITE_API_BASE_URL=http://localhost:9000/admin no .env.local
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/admin',
  timeout: 30_000,
})

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default apiClient
