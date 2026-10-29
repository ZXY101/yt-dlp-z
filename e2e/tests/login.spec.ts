import {
  completeSetupViaApi,
  expect,
  expectNoHorizontalScroll,
  signIn,
  test,
} from "../fixtures/app";

test.describe("login", () => {
  test.beforeEach(async ({ request }) => {
    await completeSetupViaApi(request);
  });

  test("signed-out visitors are sent to the login page", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    await expectNoHorizontalScroll(page);
  });

  test("a wrong password shows an error", async ({ page }) => {
    await signIn(page, "not-the-password");
    await expect(page.getByText("Incorrect password")).toBeVisible();
    await expect(page).toHaveURL(/\/login$/);
  });

  test("signing in and out", async ({ page }) => {
    await signIn(page);
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/login$/);
    await page.goto("/");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("setup cannot be repeated once complete", async ({ page }) => {
    await signIn(page);
    await page.goto("/setup");
    await expect(page).toHaveURL(/\/$/);
  });
});
