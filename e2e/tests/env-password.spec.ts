import { ENV_ADMIN_PASSWORD } from "../playwright.config";
import { expect, test } from "../fixtures/app";

test.describe("setup with YTDLPZ_ADMIN_PASSWORD", () => {
  test("setup asks for the configured password instead of creating one", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/setup$/);
    await expect(page.getByLabel("Repeat password")).toHaveCount(0);
    await expect(page.getByText(/YTDLPZ_ADMIN_PASSWORD/)).toBeVisible();

    await page.getByLabel("Admin password").fill("a-wrong-guess");
    await page.getByRole("button", { name: "Finish setup" }).click();
    await expect(page.getByText("Incorrect password")).toBeVisible();
    await expect(page).toHaveURL(/\/setup$/);

    await page.getByLabel("Admin password").fill(ENV_ADMIN_PASSWORD);
    await page.getByRole("button", { name: "Finish setup" }).click();
    await expect(page.getByRole("heading", { name: "Download", exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Sign out" }).click();
    await page.getByLabel("Password").fill(ENV_ADMIN_PASSWORD);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("heading", { name: "Download", exact: true })).toBeVisible();
  });
});
