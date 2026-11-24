import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: 1,
  reporter: [['list'], ['html',{open:'never',outputFolder:'playwright-report'}]],
  use: {baseURL:'http://127.0.0.1:4173',trace:'retain-on-failure'},
  projects:[{name:'chromium',use:{...devices['Desktop Chrome']}}],
  webServer: {
    command:'npm run build && npm run preview -- --host 127.0.0.1 --port 4173',
    url:'http://127.0.0.1:4173',
    reuseExistingServer:!process.env.CI,
    timeout:120_000,
    env:{VITE_DEMO_MODE:'true'}
  }
});
