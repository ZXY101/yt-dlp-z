import { type Page } from "@playwright/test";
import { existsSync, readFileSync } from "node:fs";

import {
  completeSetupViaApi,
  expect,
  expectNoHorizontalScroll,
  signIn,
  test,
} from "../fixtures/app";

// URLs drive the fake yt-dlp's behaviour (see e2e/stub/fake_yt_dlp.py).
const STREAM_URL = "https://example.com/watch/stream";
const BAD_CHAT_URL = "https://example.com/watch/badchat";

async function downloadWithChat(page: Page, url: string, mode: "save" | "overlay") {
  await page.goto("/");
  await page.getByLabel("Link").fill(url);
  await page.getByLabel("Live chat").selectOption(mode);
  await page.getByRole("button", { name: "Download" }).click();
  await expect(page).toHaveURL(/\/queue$/);
}

async function savedVideoPath(page: Page) {
  const saved = page.getByRole("list", { name: "Finished" }).getByText(/^Saved to /);
  const text = await saved.textContent();
  return (text ?? "").replace("Saved to ", "");
}

test.describe("live chat", () => {
  test.beforeEach(async ({ page, request }) => {
    await completeSetupViaApi(request);
    await signIn(page);
    await expect(page.getByRole("heading", { name: "Download", exact: true })).toBeVisible();
  });

  test("a stream's chat is saved with an overlay named like the video", async ({ page }) => {
    await downloadWithChat(page, STREAM_URL, "overlay");
    const finished = page.getByRole("list", { name: "Finished" });
    await expect(finished.getByText("Live chat saved, with an overlay.")).toBeVisible();

    const video = await savedVideoPath(page);
    const base = video.replace(/\.mp4$/, "");
    expect(existsSync(`${base}.live_chat.json`)).toBe(true);
    expect(readFileSync(`${base}.ass`, "utf8")).toContain("first comment");
    await expectNoHorizontalScroll(page);
  });

  test("the overlay can be rebuilt later with another look", async ({ page }, testInfo) => {
    // Its own video per project: downloads stay on disk, and this one starts without an overlay.
    await downloadWithChat(page, `https://example.com/watch/${testInfo.project.name}saved`, "save");
    const finished = page.getByRole("list", { name: "Finished" });
    await expect(finished.getByText("Live chat saved.")).toBeVisible();
    const base = (await savedVideoPath(page)).replace(/\.mp4$/, "");
    expect(existsSync(`${base}.ass`)).toBe(false);

    await finished.getByRole("button", { name: /^Chat overlay of/ }).click();
    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Text size").fill("64");
    await expectNoHorizontalScroll(page);
    await dialog.getByRole("button", { name: "Rebuild overlay" }).click();

    await expect(finished.getByText("Live chat saved, with an overlay.")).toBeVisible();
    await expect(dialog).toBeHidden();
    expect(readFileSync(`${base}.ass`, "utf8")).toContain(",64,&H");
  });

  test("a recording saves its chat as it goes", async ({ page }, testInfo) => {
    const id = `${testInfo.project.name}-slow-live`;
    const created = await page.request.post("/api/jobs", {
      data: {
        url: `https://example.com/watch/${id}`,
        recording: { from_start: false },
        live_chat: { mode: "overlay" },
      },
    });
    expect(created.status()).toBe(201);
    await page.goto("/queue");
    const inProgress = page.getByRole("list", { name: "In progress" });
    await expect(inProgress.getByText(/saving live chat/)).toBeVisible();
    await page.waitForTimeout(1000);
    await inProgress.getByRole("button", { name: /^Cancel/ }).click();

    const finished = page.getByRole("list", { name: "Finished" });
    await expect(finished.getByText("Live chat saved, with an overlay.")).toBeVisible();
    const base = (await savedVideoPath(page)).replace(/\.mp4$/, "");
    expect(readFileSync(`${base}.ass`, "utf8")).toContain("live comment");
    await expectNoHorizontalScroll(page);
  });

  test("a chat that fails leaves the download done", async ({ page }) => {
    await downloadWithChat(page, BAD_CHAT_URL, "overlay");
    const finished = page.getByRole("list", { name: "Finished" });
    await expect(finished.getByText(/live chat isn't complete/)).toBeVisible();
    await expect(finished.getByText("Done")).toBeVisible();
    const video = await savedVideoPath(page);
    expect(existsSync(video)).toBe(true);
  });

  test("a preset keeps its chat settings across a reload", async ({ page }) => {
    await page.goto("/presets/new");
    await page.getByLabel("Name", { exact: true }).fill("Streams");
    await page.getByLabel("Live chat").selectOption("overlay");
    await page.getByRole("button", { name: "Overlay look" }).click();
    await page.getByLabel("Most comments on screen").fill("20");
    await expectNoHorizontalScroll(page);
    await page.getByRole("button", { name: "Save preset" }).click();
    await expect(page.getByText(/makes a chat overlay/)).toBeVisible();

    await page.reload();
    await page.getByRole("link", { name: /Edit/ }).first().click();
    await expect(page.getByLabel("Live chat")).toHaveValue("overlay");
    await page.getByRole("button", { name: "Overlay look" }).click();
    await expect(page.getByLabel("Most comments on screen")).toHaveValue("20");
  });
});
