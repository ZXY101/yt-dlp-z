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

  test("every page has the same width", async ({ page }, testInfo) => {
    // Regression: the queue spread across the whole window while other pages stayed narrow.
    test.skip(testInfo.project.name !== "desktop", "only differs on wide screens");
    async function headingBox(name: string) {
      // The header row spans the page; the heading itself is only as wide as its text.
      const heading = page.getByRole("heading", { name, exact: true, level: 1 });
      const box = await heading.locator("..").boundingBox();
      return { x: box?.x, width: box?.width };
    }
    const download = await headingBox("Download");
    await page
      .getByRole("navigation", { name: "Main" })
      .getByRole("link", { name: "Queue" })
      .click();
    expect(await headingBox("Queue")).toEqual(download);
  });

  test("buttons show a pointer cursor", async ({ page }) => {
    // Regression: Tailwind v4 resets buttons to the default arrow cursor.
    const cursor = await page
      .getByRole("button", { name: "Advanced options" })
      .evaluate((button) => getComputedStyle(button).cursor);
    expect(cursor).toBe("pointer");
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
