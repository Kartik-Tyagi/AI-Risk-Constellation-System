// @ts-check
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.js',

  // Run tests sequentially (one browser at a time) to avoid port conflicts
  fullyParallel: false,
  workers: 1,

  // Retry on CI
  retries: process.env.CI ? 2 : 0,

  // Base URL for the running frontend
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // Generous timeout for slow CI machines
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },

  // Global timeout per test
  timeout: 60_000,
  expect: { timeout: 10_000 },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // HTML report
  reporter: [
    ['list'],
    ['html', { outputFolder: 'e2e-report', open: 'never' }],
  ],
});
