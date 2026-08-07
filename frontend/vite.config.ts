import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    assetsDir: "static",
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/assets': 'http://127.0.0.1:8000',
      '/output': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000',
    },
  },
})
