import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/paciente-ui/',
  build: {
    outDir: '../../packages/intellicare-core/intellicare_core/static/paciente-ui',
    emptyOutDir: true,
  },
  server: {
    port: 5177,
    proxy: {
      '/cuidado': 'http://localhost:9000',
      '/health': 'http://localhost:9000',
    },
  },
})

