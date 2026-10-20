import {defineConfig} from '@playwright/test';
import {fileURLToPath} from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
export default defineConfig({
  testDir: './browser', timeout: 30000, workers: 1,
  projects: [
    {name: 'desktop', use: {viewport: {width: 1280, height: 720}}},
    {name: 'phone', use: {viewport: {width: 390, height: 844}}}
  ],
  use: {baseURL: 'http://127.0.0.1:4213', reducedMotion: 'reduce',
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
      ? {executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {}},
  webServer: [{command: 'python3 -m http.server 4213 --bind 127.0.0.1 --directory webapp',
    cwd: root, url: 'http://127.0.0.1:4213', reuseExistingServer: false}, {command: 'python3 -m http.server 4214 --bind 127.0.0.1 --directory tools/lidar_wound_progress/webapp', cwd: root, url: 'http://127.0.0.1:4214', reuseExistingServer: false}]
});
