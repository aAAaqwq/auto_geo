// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright 配置
 * 测试文件路径指向根目录的 tests/fronted_tests
 */
module.exports = defineConfig({
  testDir: '../tests/fronted_tests',

  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  reporter: 'html',

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
