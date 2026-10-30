import type { Page } from "@playwright/test";

import {
  completeSetupViaApi,
  expect,
  expectNoHorizontalScroll,
  signIn,
  test,
} from "../fixtures/app";
import { FAKE_COOKIES, NOT_COOKIES } from "../fixtures/files";

async function upload(page: Page, name = "Members") {
  await page.getByLabel("Name").fill(name);
  await page.getByLabel("Cookies file").setInputFiles(FAKE_COOKIES);
  await page.getByRole("button", { name: "Upload" }).click();
}

test.describe("cookies", () => {
  test.beforeEach(async ({ page, request }) => {
    await completeSetupViaApi(request);
    await signIn(page);
    await expect(page.getByRole("heading", { name: "Download", exact: true })).toBeVisible();
    await page.goto("/cookies");
  });

  test("an uploaded cookies file is used for downloads", async ({ page }) => {
    await expect(page.getByText("No cookies yet")).toBeVisible();
    await upload(page);
    const list = page.getByRole("list", { name: "Cookies files" });
    await expect(list.getByText("2 cookies for example.com, example.org")).toBeVisible();
    await expect(page.getByText("fake-e2e-session")).toHaveCount(0);
    await expectNoHorizontalScroll(page);

    await page.goto("/");
    await page.getByLabel("Link").fill("https://example.com/watch/members");
    await page.getByLabel("Cookies").selectOption({ label: "Members" });
    await page.getByRole("button", { name: "Download" }).click();
    const finished = page.getByRole("list", { name: "Finished" });
    await expect(finished.getByText("Done")).toBeVisible();
    await finished.getByRole("button", { name: "Log" }).click();
    await expect(page.getByRole("dialog").getByText("[fake] cookies: 2")).toBeVisible();
  });

  test("the test button reports whether the cookies sign in", async ({ page }) => {
    await upload(page);
    await page.getByRole("button", { name: "Test" }).click();
    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Page to open").fill("https://example.com/watch/members");
    await dialog.getByRole("button", { name: "Test" }).click();
    await expect(dialog.getByText("Opened “Fake video members” with these cookies.")).toBeVisible();

    await dialog.getByLabel("Page to open").fill("https://example.com/watch/fail");
    await dialog.getByRole("button", { name: "Test" }).click();
    await expect(dialog.getByText(/Sign in to confirm/)).toBeVisible();
  });

  test("files that aren't cookies.txt are refused", async ({ page }) => {
    await page.getByLabel("Name").fill("Wrong");
    await page.getByLabel("Cookies file").setInputFiles(NOT_COOKIES);
    await page.getByRole("button", { name: "Upload" }).click();
    await expect(page.getByText(/isn't in Netscape cookies.txt format/)).toBeVisible();
    await expect(page.getByText("fake-e2e-session")).toHaveCount(0);
  });

  test("cookies can be replaced and deleted", async ({ page }) => {
    await upload(page);
    await page.getByLabel("New cookies file for Members").setInputFiles({
      ...FAKE_COOKIES,
      buffer: Buffer.from(".example.net\tTRUE\t/\tTRUE\t0\tSID\tfake-e2e-new"),
    });
    await expect(page.getByText("1 cookie for example.net")).toBeVisible();

    await page.getByRole("button", { name: "Delete Members" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();
    await expect(page.getByText("No cookies yet")).toBeVisible();
    await page.reload();
    await expect(page.getByText("No cookies yet")).toBeVisible();
  });
});
