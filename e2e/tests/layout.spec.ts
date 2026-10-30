import {
  completeSetupViaApi,
  expect,
  expectNoHorizontalScroll,
  signIn,
  test,
} from "../fixtures/app";

test.describe("app layout", () => {
  test.beforeEach(async ({ page, request }) => {
    await completeSetupViaApi(request);
    await signIn(page);
    await expect(page.getByRole("heading", { name: "Download", exact: true })).toBeVisible();
  });

  test("desktop shows the sidebar navigation", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop", "desktop-only layout");
    await expect(page.getByRole("navigation", { name: "Main" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Open menu" })).toBeHidden();
    await expectNoHorizontalScroll(page);
  });

  test("dark mode also darkens native controls", async ({ page }) => {
    // Regression: select popups stayed white with light text in dark mode.
    await page.emulateMedia({ colorScheme: "dark" });
    const scheme = await page.evaluate(
      () => getComputedStyle(document.documentElement).colorScheme,
    );
    expect(scheme).toBe("dark");
  });

  test("mobile uses a slide-out menu", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "mobile", "mobile-only layout");
    await expect(page.getByRole("navigation", { name: "Main" })).toBeHidden();
    await expectNoHorizontalScroll(page);

    await page.getByRole("button", { name: "Open menu" }).click();
    const menu = page.getByRole("dialog");
    await expect(menu.getByRole("link", { name: "Download", exact: true })).toBeVisible();

    await menu.getByRole("link", { name: "Queue" }).click();
    await expect(menu).toBeHidden();
    await expect(page.getByRole("heading", { name: "Queue" })).toBeVisible();
  });
});
