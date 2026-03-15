import axios, { InternalAxiosRequestConfig } from 'axios'
import { getToken } from '../auth/tokenRef'

// baseURL vazio — os paths já incluem o prefixo do módulo (/admin/..., /gestor/..., etc.)
// Combinar baseURL='/admin' + path='/admin/tenants' geraria duplo prefixo /admin/admin/tenants.
// Em dev com npm run dev, definir VITE_API_BASE_URL=http://localhost:9000 no .env.local
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
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
