import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// Development server only: requests to /api go to the backend, so the app
// uses the same origin in development as behind nginx in the containers
// (DECISIONS.md D-052). Point AEGIS_DEV_API_URL elsewhere if needed.
const devApiUrl = process.env['AEGIS_DEV_API_URL'] ?? 'http://127.0.0.1:8000'

// https://vite.dev/config/ and https://vitest.dev/config/
// Vitest reuses this configuration, so tests are transformed exactly like the app.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': { target: devApiUrl, changeOrigin: false },
    },
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
    setupFiles: ['./src/test/setup.ts'],
    // Spies and mocks are restored after every test, so tests stay independent.
    restoreMocks: true,
    unstubGlobals: true,
  },
})
