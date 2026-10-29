import { ADMIN_PASSWORD, expect, expectNoHorizontalScroll, test } from "../fixtures/app";

test.describe("first-run setup", () => {
  test("a fresh install leads through setup into the dashboard", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/setup$/);
    await expect(page.getByRole("heading", { name: "Welcome to yt-dlp-z" })).toBeVisible();
    await expect(page.getByLabel("Download folder")).not.toHaveValue("");
    await expectNoHorizontalScroll(page);

    await page.getByLabel("Admin password").fill(ADMIN_PASSWORD);
    await page.getByLabel("Repeat password").fill(ADMIN_PASSWORD);
    await page.getByRole("button", { name: "Finish setup" }).click();

    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await page.reload();
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  });

  test("invalid input is explained and nothing is saved", async ({ page }) => {
    await page.goto("/setup");
    await page.getByLabel("Admin password").fill("short");
    await page.getByLabel("Download folder").fill("relative/folder");
    await page.getByRole("button", { name: "Finish setup" }).click();

    await expect(page.getByText("Use at least 8 characters.")).toBeVisible();
    await expect(page.getByText("Use a full path, e.g. /downloads.")).toBeVisible();
    await expectNoHorizontalScroll(page);

    await page.reload();
    await expect(page).toHaveURL(/\/setup$/);
  });

  test("an unusable download folder is rejected by the server", async ({ page }) => {
    await page.goto("/setup");
    await page.getByLabel("Admin password").fill(ADMIN_PASSWORD);
    await page.getByLabel("Repeat password").fill(ADMIN_PASSWORD);
    await page.getByLabel("Download folder").fill("/proc/yt-dlp-z-not-allowed");
    await page.getByRole("button", { name: "Finish setup" }).click();

    await expect(page.getByText(/Cannot create download folder/)).toBeVisible();
    await expect(page).toHaveURL(/\/setup$/);
  });
});
