import { defineConfig, devices } from '@playwright/test';

/**
 * FlightAI Playwright Configuration
 * Tests both frontend (browser) and backend API (request)
 */
export default defineConfig({
  testDir: './tests',
  fullyParallel: false, // Run sequentially so auth state carries over
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['html', { outputFolder: 'playwright-report' }], ['list']],

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Start frontend dev server before tests
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:3000',
  //   reuseExistingServer: true,
  //   cwd: './frontend',
  // },
});
