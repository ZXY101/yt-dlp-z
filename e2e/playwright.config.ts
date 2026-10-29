import { defineConfig, devices } from "@playwright/test";

const PORT = 8765;
export const BASE_URL = `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: "tests",
  // Tests share one server and reset its state, so they must not run in parallel.
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } },
    },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
  webServer: {
    command: "./scripts/start-server.sh",
    env: { PORT: String(PORT) },
    url: `${BASE_URL}/api/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
