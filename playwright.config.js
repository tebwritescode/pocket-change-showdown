// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './tests',
  fullyParallel: false, // Run tests sequentially to avoid database conflicts
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker to avoid database conflicts
  reporter: [
    ['html', { outputFolder: './playwright-report' }],
    ['json', { outputFile: './test-results/results.json' }],
    ['list']
  ],
  use: {
    baseURL: 'http://localhost:5001',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: true,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'source venv/bin/activate && python app.py',
    port: 5001,
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000, // 2 minutes
    cwd: '/Users/timbruening/Documents/Projects/claude-code/pcs-tracker',
    env: {
      FLASK_ENV: 'development',
      FLASK_DEBUG: 'false',
      PYTHONUNBUFFERED: '1'
    }
  },
});