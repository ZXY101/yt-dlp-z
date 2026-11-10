import { defineConfig, devices } from "@playwright/test";

const PORT = 8765;
// A second server started with YTDLPZ_ADMIN_PASSWORD, for the env-password setup flow.
const ENV_PASSWORD_PORT = 8766;
export const ENV_ADMIN_PASSWORD = "e2e-env-password";

function serverUrl(port: number) {
  return `http://127.0.0.1:${port}`;
}

export default defineConfig({
  testDir: "tests",
  // Tests share servers and reset their state, so they must not run in parallel.
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: serverUrl(PORT),
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "desktop",
      testIgnore: [/env-password/, /extension/],
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } },
    },
    { name: "mobile", testIgnore: [/env-password/, /extension/], use: { ...devices["Pixel 7"] } },
    // Loads the built browser extension into its own Chromium (see fixtures/extension.ts).
    { name: "extension", testMatch: /extension/ },
    {
      name: "env-password",
      testMatch: /env-password/,
      use: { ...devices["Desktop Chrome"], baseURL: serverUrl(ENV_PASSWORD_PORT) },
    },
  ],
  webServer: [
    {
      command: "./scripts/start-server.sh",
      env: { PORT: String(PORT) },
      url: `${serverUrl(PORT)}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: "./scripts/start-server.sh",
      // The first server builds the frontend; tests only start once both are healthy.
      env: {
        PORT: String(ENV_PASSWORD_PORT),
        SKIP_FRONTEND_BUILD: "1",
        YTDLPZ_ADMIN_PASSWORD: ENV_ADMIN_PASSWORD,
      },
      url: `${serverUrl(ENV_PASSWORD_PORT)}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
