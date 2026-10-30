import { type APIRequestContext, type Page, expect, test as base } from "@playwright/test";

export const ADMIN_PASSWORD = "e2e-admin-password";

async function resetServer(request: APIRequestContext) {
  const response = await request.post("/api/test/reset");
  expect(response.status()).toBe(204);
}

/** Completes first-run setup through the API, leaving the browser signed out. */
export async function completeSetupViaApi(request: APIRequestContext) {
  const status = await (await request.get("/api/auth/status")).json();
  const response = await request.post("/api/auth/setup", {
    data: { password: ADMIN_PASSWORD, download_dir: status.default_download_dir },
  });
  expect(response.status()).toBe(204);
}

/** Serves a fake YouTube feed for a channel, newest entry first. */
export async function setFeed(request: APIRequestContext, channelId: string, videoIds: string[]) {
  const entries = videoIds.map((id) => ({ video_id: id, title: `Feed ${id}` }));
  const response = await request.put(`/api/test/feeds/${channelId}`, { data: entries });
  expect(response.status()).toBe(204);
}

export async function signIn(page: Page, password = ADMIN_PASSWORD) {
  await page.goto("/login");
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
}

export async function expectNoHorizontalScroll(page: Page) {
  const overflows = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(overflows).toBe(false);
}

// Auto fixtures run before every test and its hooks, so each test starts from a fresh install.
export const test = base.extend<{ freshServer: void }>({
  freshServer: [
    async ({ request }, run) => {
      await resetServer(request);
      await run();
    },
    { auto: true },
  ],
});

export { expect };
