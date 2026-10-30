import {
  completeSetupViaApi,
  expect,
  expectNoHorizontalScroll,
  signIn,
  test,
} from "../fixtures/app";

test.describe("settings", () => {
  test.beforeEach(async ({ page, request }) => {
    await completeSetupViaApi(request);
    await signIn(page);
    await expect(page.getByRole("heading", { name: "Download", exact: true })).toBeVisible();
    await page.goto("/settings");
  });

  test("changes are saved and used for new downloads", async ({ page }) => {
    const folder = page.getByLabel("Download folder");
    const newFolder = `${await folder.inputValue()}/moved`;
    await folder.fill(newFolder);
    await page.getByLabel("Downloads at the same time").fill("1");
    await page.getByLabel("Recordings at the same time").fill("3");
    await page.getByLabel("New file every (hours)").fill("");
    await page.getByLabel("Stop after (hours)").fill("12");
    await page.getByRole("button", { name: "Save settings" }).click();
    await expect(page.getByText("Settings saved.")).toBeVisible();
    await expectNoHorizontalScroll(page);

    await page.reload();
    await expect(page.getByLabel("Download folder")).toHaveValue(newFolder);
    await expect(page.getByLabel("Downloads at the same time")).toHaveValue("1");
    await expect(page.getByLabel("Recordings at the same time")).toHaveValue("3");
    await expect(page.getByLabel("New file every (hours)")).toHaveValue("");
    await expect(page.getByLabel("Stop after (hours)")).toHaveValue("12");

    await page.goto("/");
    await page.getByLabel("Link").fill("https://example.com/watch/moved");
    await page.getByRole("button", { name: "Download" }).click();
    await expect(page.getByText(/Saved to .*\/moved\/Fake video moved/)).toBeVisible();
  });

  test("invalid values are explained", async ({ page }) => {
    await page.getByLabel("Downloads at the same time").fill("50");
    await page.getByRole("button", { name: "Save settings" }).click();
    await expect(page.getByText("Enter a whole number from 1 to 10.")).toBeVisible();

    await page.getByLabel("Downloads at the same time").fill("2");
    await page.getByLabel("Download folder").fill("relative/folder");
    await page.getByRole("button", { name: "Save settings" }).click();
    await expect(page.getByText(/must be an absolute path/)).toBeVisible();
  });
});
