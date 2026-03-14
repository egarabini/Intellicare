import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/clinico-ui/',
  build: {
    outDir: '../../packages/intellicare-core/intellicare_core/static/clinico-ui',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/cuidado': 'http://localhost:8000',
      '/gestor': 'http://localhost:8000',
      '/slm': 'http://localhost:8000',
      '/vector': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
    },
  },
})
