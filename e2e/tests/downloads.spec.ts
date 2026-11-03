import { type Page } from "@playwright/test";

import {
  completeSetupViaApi,
  expect,
  expectNoHorizontalScroll,
  signIn,
  test,
} from "../fixtures/app";

// URLs drive the fake yt-dlp's behaviour (see e2e/stub/fake_yt_dlp.py).
const QUICK_URL = "https://example.com/watch/quick";
const FAILING_URL = "https://example.com/watch/fail";
const SLOW_URL = "https://example.com/watch/slow";

async function startDownload(page: Page, url: string) {
  await page.goto("/");
  await page.getByLabel("Link").fill(url);
  await page.getByRole("button", { name: "Download" }).click();
  await expect(page).toHaveURL(/\/queue$/);
}

test.describe("downloads", () => {
  test.beforeEach(async ({ page, request }) => {
    await completeSetupViaApi(request);
    await signIn(page);
    await expect(page.getByRole("heading", { name: "Download", exact: true })).toBeVisible();
  });

  test("a download runs to completion", async ({ page }) => {
    await page.goto("/");
    await expectNoHorizontalScroll(page);
    await page.getByLabel("Link").fill(QUICK_URL);
    await page.getByLabel("Save to").fill("e2e");
    await page.getByLabel("Quality").selectOption("1080p");
    await page.getByRole("button", { name: "Download" }).click();

    const finished = page.getByRole("list", { name: "Finished" });
    await expect(finished.getByText("Fake video quick", { exact: true })).toBeVisible();
    await expect(finished.getByText("Done")).toBeVisible();
    await expect(
      finished.getByText(/Saved to .*\/e2e\/Fake video quick \[quick\]\.mp4/),
    ).toBeVisible();
    await expectNoHorizontalScroll(page);
  });

  test("the log of a long title fits on a phone", async ({ page }) => {
    // Regression: a truncated title widened the dialog past the screen edge.
    const longId = "ガルガンターテイム初めてのホロ鯖ARK".repeat(2);
    await startDownload(page, `https://example.com/watch/${longId}`);
    const finished = page.getByRole("list", { name: "Finished" });
    await finished.getByRole("button", { name: "Log" }).click();
    const dialog = page.getByRole("dialog");
    const text = dialog.getByText(/\[fake\] done/);
    await expect(text).toBeVisible();
    // The dialog itself is capped at the screen width; its content used to spill past it.
    const dialogBox = await dialog.boundingBox();
    const textBox = await text.boundingBox();
    expect(dialogBox && textBox && textBox.x + textBox.width <= dialogBox.x + dialogBox.width).toBe(
      true,
    );
  });

  test("a failed download explains why and can be retried", async ({ page }) => {
    await startDownload(page, FAILING_URL);
    const finished = page.getByRole("list", { name: "Finished" });
    await expect(finished.getByText("[fake] This video is unavailable")).toBeVisible();

    await finished.getByRole("button", { name: "Log" }).click();
    const log = page.getByRole("dialog");
    await expect(log.getByText(/ERROR: \[fake\] This video is unavailable/)).toBeVisible();
    await page.keyboard.press("Escape");

    await finished.getByRole("button", { name: "Retry Fake video fail" }).click();
    await expect(finished.getByText("Failed")).toBeVisible();
  });

  test("a running download can be cancelled from the queue", async ({ page }) => {
    await startDownload(page, SLOW_URL);
    const active = page.getByRole("list", { name: "In progress" });
    await expect(active.getByText(/% · /)).toBeVisible();
    await expect(active.getByText("Downloading")).toBeVisible();
    await expectNoHorizontalScroll(page);
    await active.getByRole("button", { name: "Cancel Fake video slow" }).click();

    await expect(active).toBeHidden();
    await expect(page.getByRole("list", { name: "Finished" }).getByText("Cancelled")).toBeVisible();
  });

  test("blocked yt-dlp options are refused", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Link").fill(QUICK_URL);
    await page.getByRole("button", { name: "Advanced options" }).click();
    await page.getByLabel("Extra yt-dlp options").fill("--exec 'touch /tmp/pwned'");
    await page.getByRole("button", { name: "Download" }).click();

    await expect(page.getByText(/--exec isn't allowed/)).toBeVisible();
    await expect(page).toHaveURL(/:\d+\/$/);
  });

  test("any yt-dlp option can be set from the full list", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Link").fill(QUICK_URL);
    await page.getByRole("button", { name: "Advanced options" }).click();
    await page.getByRole("button", { name: /All yt-dlp options/ }).click();
    const dialog = page.getByRole("dialog", { name: "yt-dlp options" });
    await expect(dialog.getByLabel("Search options")).toBeVisible();
    // Groups are tabs on wide screens and a picker on phones.
    if (await dialog.getByRole("tab", { name: "Network" }).isVisible()) {
      await dialog.getByRole("tab", { name: "Network" }).click();
    } else {
      await dialog.getByLabel("Option group", { exact: true }).selectOption("Network Options");
    }
    await expect(dialog.getByLabel(/^--proxy/)).toBeVisible();
    await expectNoHorizontalScroll(page);
    await page.getByLabel("Search options").fill("limit-rate");
    await page.getByLabel(/^--limit-rate/).fill("1M");
    await expect(page.getByLabel("--exec CMD")).toHaveCount(0);
    await page.getByLabel("Search options").fill("--exec");
    await expect(page.getByLabel(/^--exec/).first()).toBeDisabled();
    await dialog.getByRole("button", { name: "Done" }).click();
    await expect(page.getByRole("button", { name: /All yt-dlp options/ })).toContainText("set");
    await page.getByRole("button", { name: "Download" }).click();

    const finished = page.getByRole("list", { name: "Finished" });
    await finished.getByRole("button", { name: "Log" }).click();
    await expect(page.getByRole("dialog").getByText(/--limit-rate 1M/)).toBeVisible();
  });

  test("a video link from a playlist downloads just that video by default", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Link").fill("https://www.youtube.com/watch?v=inlist&list=PLfake");
    await expect(page.getByLabel("Just this video")).toBeChecked();
    await expectNoHorizontalScroll(page);
    await page.getByRole("button", { name: "Download" }).click();

    const finished = page.getByRole("list", { name: "Finished" });
    await finished.getByRole("button", { name: "Log" }).click();
    await expect(page.getByRole("dialog").getByText(/--no-playlist/)).toBeVisible();
  });

  test("the whole playlist can be chosen instead", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Link").fill("https://youtu.be/inlist?list=PLfake");
    await page.getByLabel("The whole playlist").check();
    await page.getByRole("button", { name: "Download" }).click();

    const finished = page.getByRole("list", { name: "Finished" });
    await finished.getByRole("button", { name: "Log" }).click();
    const log = page.getByRole("dialog");
    await expect(log.getByText(/--yes-playlist/)).toBeVisible();
    await expect(log.getByText(/--no-playlist/)).toHaveCount(0);
  });

  test("playlist and channel links warn that every video is downloaded", async ({ page }) => {
    await page.goto("/");
    const link = page.getByLabel("Link");
    await link.fill("https://www.youtube.com/playlist?list=PLfake");
    await expect(page.getByText(/all 24 videos in it/)).toBeVisible();
    await link.fill("https://www.youtube.com/@someone/videos");
    await expect(page.getByText(/every video, Short and stream/)).toBeVisible();
    await expectNoHorizontalScroll(page);
    await link.fill(QUICK_URL);
    await expect(page.getByLabel("Media details")).toContainText("Fake video quick");
    await expect(page.getByText(/will be downloaded/)).toHaveCount(0);
  });

  test("a link yt-dlp can't open is caught before downloading", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Link").fill("https://example.com/watch/broken");
    await expect(
      page.getByText(/Can't download this link: This video is unavailable/),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Download" })).toBeDisabled();
  });

  test("a live stream can be recorded from the download page", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Link").fill("https://www.youtube.com/watch?v=live-e2e");
    await expect(page.getByLabel("Media details")).toContainText("Live now");
    await page.getByLabel("From now").check();
    await expectNoHorizontalScroll(page);
    await page.getByRole("button", { name: "Record" }).click();

    await expect(page).toHaveURL(/\/queue$/);
    await expect(page.getByText("Recording", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Cancel Fake video live-e2e" }).click();
  });

  test("an upcoming stream gets a scheduled recording", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Link").fill("https://www.youtube.com/watch?v=upcoming-e2e");
    await expect(page.getByText(/starts when the stream does/)).toBeVisible();
    await page.getByRole("button", { name: "Schedule recording" }).click();

    const scheduled = page.getByRole("list", { name: "Scheduled" });
    await expect(scheduled.getByText("Fake video upcoming-e2e")).toBeVisible();
  });

  test("save to suggests folders that already exist", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Link").fill(QUICK_URL);
    await page.getByLabel("Save to").fill("shows/season 1");
    await page.getByRole("button", { name: "Download" }).click();
    await expect(page.getByRole("list", { name: "Finished" }).getByText("Done")).toBeVisible();

    await page.goto("/");
    const field = page.getByLabel("Save to");
    await field.click();
    await page.getByRole("option", { name: "shows", exact: true }).click();
    await expect(field).toHaveValue("shows/");
    await page.getByRole("option", { name: "shows/season 1" }).click();
    await expect(field).toHaveValue("shows/season 1/");
    await expect(page.getByRole("listbox", { name: "Existing folders" })).toBeHidden();
  });

  test("finished downloads can be removed from the list", async ({ page }) => {
    await startDownload(page, QUICK_URL);
    const finished = page.getByRole("list", { name: "Finished" });
    await finished.getByRole("button", { name: "Remove Fake video quick from the list" }).click();
    await expect(page.getByText("No downloads yet")).toBeVisible();
  });
});
