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
    await page.getByRole("button", { name: "Save settings" }).click();
    await expect(page.getByText("Settings saved.")).toBeVisible();
    await expectNoHorizontalScroll(page);

    await page.reload();
    await expect(page.getByLabel("Download folder")).toHaveValue(newFolder);
    await expect(page.getByLabel("Downloads at the same time")).toHaveValue("1");
    await expect(page.getByLabel("Recordings at the same time")).toHaveValue("3");

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

  test("yt-dlp can be updated and put back to the bundled version", async ({ page }) => {
    const section = page.getByRole("region", { name: "yt-dlp" });
    await expect(section.getByText(/bundled with the app/)).toBeVisible();
    await section.getByLabel("Update channel").selectOption("nightly");
    await section.getByRole("button", { name: "Check for updates" }).click();
    await expect(section.getByText("yt-dlp 2099.1.2.dev0 is available.")).toBeVisible();
    await section.getByRole("button", { name: "Update now" }).click();
    await expect(section.getByText("Updated yt-dlp to 2099.1.2.dev0.")).toBeVisible();
    await expect(section.getByText(/Version 2099.1.2.dev0, updated/)).toBeVisible();
    await expectNoHorizontalScroll(page);

    await section.getByRole("button", { name: "Use bundled version" }).click();
    await expect(section.getByText(/bundled with the app/)).toBeVisible();
    await section.getByLabel("Update channel").selectOption("stable");

    // click(), not check(): the box follows the saved setting a moment after the click.
    const autoUpdate = section.getByLabel("Update automatically");
    await autoUpdate.click();
    await expect(autoUpdate).toBeChecked();
    await page.reload();
    await expect(autoUpdate).toBeChecked();
    await autoUpdate.click();
    await expect(autoUpdate).not.toBeChecked();
  });

  test("ntfy notifications are tested, saved and sent", async ({ page, request }) => {
    const section = page.getByRole("region", { name: "Notifications" });
    const server = `${new URL(page.url()).origin}/api/test/ntfy`;
    await section.getByLabel("Server").fill(server);
    await section.getByLabel("Topic").fill("e2e-downloads");
    await section.getByLabel("Access token").fill("tk_e2e");
    await section.getByRole("button", { name: "Send test message" }).click();
    await expect(section.getByText("Test message sent. Check your phone.")).toBeVisible();
    await section.getByLabel("Recording started").click();
    await section.getByRole("button", { name: "Save notifications" }).click();
    await expect(section.getByText("Notification settings saved.")).toBeVisible();
    await expect(
      section.getByText("A token is saved. Type a new one to replace it."),
    ).toBeVisible();
    await expectNoHorizontalScroll(page);

    await page.goto("/");
    await page.getByLabel("Link").fill("https://example.com/watch/notified");
    await page.getByRole("button", { name: "Download" }).click();
    await expect(page.getByText(/Saved to /)).toBeVisible();

    await expect
      .poll(async () => (await request.get("/api/test/ntfy")).json())
      .toEqual([
        expect.objectContaining({ topic: "e2e-downloads", message: "Notifications work." }),
        expect.objectContaining({ title: "Download finished", message: "Fake video notified" }),
      ]);
  });

  test("a PO token provider is tested, saved and turned off", async ({ page }) => {
    const section = page.getByRole("region", { name: "PO tokens" });
    const provider = `${new URL(page.url()).origin}/api/test/pot`;
    await expect(section.getByText("Off.", { exact: true })).toBeVisible();
    await section.getByLabel("Provider address").fill(provider);
    await section.getByRole("button", { name: "Test" }).click();
    await expect(section.getByText("Provider 2.0.2 answered.")).toBeVisible();
    await section.getByRole("button", { name: "Save provider" }).click();
    await expect(section.getByText("PO tokens on.")).toBeVisible();
    await expect(section.getByText("On: provider 2.0.2, plugin 2.0.2.")).toBeVisible();
    await expectNoHorizontalScroll(page);

    await page.reload();
    await expect(section.getByLabel("Provider address")).toHaveValue(provider);
    await section.getByLabel("Provider address").fill("");
    await section.getByRole("button", { name: "Save provider" }).click();
    await expect(section.getByText("PO tokens off.", { exact: true })).toBeVisible();
    await expect(section.getByText("Off.", { exact: true })).toBeVisible();
  });
});
