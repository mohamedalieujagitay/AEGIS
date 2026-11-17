import { defineConfig, devices } from '@playwright/test'

/**
 * End-to-end tests for the running application (roadmap 2.1, CLAUDE.md §10).
 *
 * They run against an AEGIS deployment that the tests may change: create
 * accounts and reset passwords. Use a disposable stack, for example the one
 * started by `infrastructure/scripts/smoke_test.py --e2e`. Never run them
 * against a deployment with real users.
 *
 * Required environment: AEGIS_E2E_ADMIN_EMAIL and AEGIS_E2E_ADMIN_PASSWORD, an
 * existing instance administrator. Optional: AEGIS_E2E_BASE_URL (default
 * http://127.0.0.1:8080).
 */
const baseURL = process.env['AEGIS_E2E_BASE_URL'] ?? 'http://127.0.0.1:8080'

export default defineConfig({
  testDir: './e2e',
  // Tests share one deployment and change its accounts: run them one at a time.
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: Boolean(process.env['CI']),
  reporter: [['list']],
  use: {
    baseURL,
    trace: 'off',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
