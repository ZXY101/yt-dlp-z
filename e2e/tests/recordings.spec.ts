import { type Page } from "@playwright/test";

import {
  completeSetupViaApi,
  expect,
  expectNoHorizontalScroll,
  setFeed,
  signIn,
  test,
} from "../fixtures/app";

// The fake yt-dlp resolves @demo to this channel id, and treats video ids containing
// "upcoming" (starts in 2100) or "live" as streams (see stub/fake_yt_dlp.py).
const DEMO_ID = "UCdemo";

async function watchStreams(page: Page) {
  await page.goto("/subscriptions/new");
  await page.getByLabel("Channel", { exact: true }).fill("@demo");
  await page.getByLabel("Download recent uploads now").fill("0");
  await page.getByLabel("Live streams and premieres").check();
  await page.getByRole("button", { name: "Save subscription" }).click();
  await expect(page.getByText(/Checked just now/)).toBeVisible();
}

test.describe("recordings", () => {
  test.beforeEach(async ({ page, request }) => {
    await completeSetupViaApi(request);
    await signIn(page);
    await expect(page.getByRole("heading", { name: "Download", exact: true })).toBeVisible();
  });

  test("streams are recorded from the start, upcoming ones when they begin", async ({
    page,
    request,
  }) => {
    await setFeed(request, DEMO_ID, []);
    await watchStreams(page);
    await setFeed(request, DEMO_ID, ["upcoming1", "live1"]);
    await page.getByRole("button", { name: "Check Fake demo now" }).click();

    await page.getByRole("link", { name: "Edit Fake demo" }).click();
    const videos = page.getByRole("list", { name: "Recent videos" });
    await expect(videos.getByText("Recording scheduled", { exact: true })).toBeVisible();
    await expect(videos.getByText("Recording", { exact: true })).toBeVisible();

    await page.goto("/queue");
    const scheduled = page.getByRole("list", { name: "Scheduled" });
    await expect(scheduled.getByText(/Stream starts .*Recording begins/)).toBeVisible();
    await expectNoHorizontalScroll(page);

    const finished = page.getByRole("list", { name: "Finished" });
    await expect(finished.getByText("Fake video live1", { exact: true })).toBeVisible();
    await finished.getByRole("button", { name: "Log" }).click();
    await expect(page.getByRole("dialog").getByText(/--live-from-start/)).toBeVisible();
  });

  test("a scheduled recording can be cancelled", async ({ page, request }) => {
    await setFeed(request, DEMO_ID, []);
    await watchStreams(page);
    await setFeed(request, DEMO_ID, ["upcoming1"]);
    await page.getByRole("button", { name: "Check Fake demo now" }).click();

    await page.goto("/queue");
    const scheduled = page.getByRole("list", { name: "Scheduled" });
    await scheduled.getByRole("button", { name: "Cancel Fake video upcoming1" }).click();
    const finished = page.getByRole("list", { name: "Finished" });
    await expect(finished.getByText("Cancelled")).toBeVisible();
    await expect(page.getByRole("list", { name: "Scheduled" })).toHaveCount(0);
  });
});
