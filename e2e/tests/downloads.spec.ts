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

  test("a failed download explains why and can be retried", async ({ page }) => {
    await startDownload(page, FAILING_URL);
    const finished = page.getByRole("list", { name: "Finished" });
    await expect(finished.getByText("[fake] This video is unavailable")).toBeVisible();

    await finished.getByRole("button", { name: "Log" }).click();
    const log = page.getByRole("dialog");
    await expect(log.getByText(/ERROR: \[fake\] This video is unavailable/)).toBeVisible();
    await page.keyboard.press("Escape");

    await finished.getByRole("button", { name: `Retry ${FAILING_URL}` }).click();
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
    await page.getByRole("button", { name: "All yt-dlp options" }).click();
    await page.getByLabel("Search options").fill("limit-rate");
    await page.getByLabel(/^--limit-rate/).fill("1M");
    await expect(page.getByLabel("--exec CMD")).toHaveCount(0);
    await page.getByLabel("Search options").fill("--exec");
    await expect(page.getByLabel(/^--exec/).first()).toBeDisabled();
    await expectNoHorizontalScroll(page);
    await page.getByRole("button", { name: "Download" }).click();

    const finished = page.getByRole("list", { name: "Finished" });
    await finished.getByRole("button", { name: "Log" }).click();
    await expect(page.getByRole("dialog").getByText(/--limit-rate 1M/)).toBeVisible();
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
    await field.fill("shows/");
    const listId = await field.getAttribute("list");
    const options = page.locator(`datalist[id="${listId}"] option`);
    await expect(options).toHaveAttribute("value", "shows/season 1");
  });

  test("finished downloads can be removed from the list", async ({ page }) => {
    await startDownload(page, QUICK_URL);
    const finished = page.getByRole("list", { name: "Finished" });
    await finished.getByRole("button", { name: "Remove Fake video quick from the list" }).click();
    await expect(page.getByText("No downloads yet")).toBeVisible();
  });
});
