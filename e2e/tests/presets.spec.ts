import {
  completeSetupViaApi,
  expect,
  expectNoHorizontalScroll,
  signIn,
  test,
} from "../fixtures/app";

test.describe("presets", () => {
  test.beforeEach(async ({ page, request }) => {
    await completeSetupViaApi(request);
    await signIn(page);
    await expect(page.getByRole("heading", { name: "Download", exact: true })).toBeVisible();
  });

  test("a default preset fills in the download form", async ({ page }) => {
    await page.goto("/presets");
    await page.getByRole("link", { name: /No presets yet/ }).click();
    await page.getByLabel("Name", { exact: true }).fill("Audio");
    await page.getByLabel("Use by default").check();
    await page.getByLabel("Quality").selectOption("audio-mp3");
    await page.getByLabel("Save to").fill("audio");
    await expectNoHorizontalScroll(page);
    await page.getByRole("button", { name: "Save preset" }).click();

    const list = page.getByRole("list", { name: "Presets" });
    await expect(list.getByText("Audio", { exact: true })).toBeVisible();
    await expect(list.getByText("Default")).toBeVisible();
    await page.reload();
    await expect(list.getByText(/Saves to audio · 4 options/)).toBeVisible();

    await page.goto("/");
    await expect(page.getByLabel("Preset")).toHaveValue(/\d+/);
    await expect(page.getByLabel("Quality")).toHaveValue("audio-mp3");
    await page.getByLabel("Link").fill("https://example.com/watch/song");
    await page.getByRole("button", { name: "Download" }).click();

    const finished = page.getByRole("list", { name: "Finished" });
    await expect(finished.getByText(/Saved to .*\/audio\/Fake video song/)).toBeVisible();
    await finished.getByRole("button", { name: "Log" }).click();
    await expect(
      page.getByRole("dialog").getByText(/--extract-audio --audio-format mp3/),
    ).toBeVisible();
  });

  test("presets can be edited and deleted", async ({ page }) => {
    await page.goto("/presets/new");
    await page.getByLabel("Name", { exact: true }).fill("Clips");
    await page.getByRole("button", { name: "Save preset" }).click();
    await page.getByRole("link", { name: "Edit Clips" }).click();
    await page.getByLabel("Name", { exact: true }).fill("Short clips");
    await page.getByLabel("Quality").selectOption("720p");
    await page.getByRole("button", { name: "Save preset" }).click();

    const list = page.getByRole("list", { name: "Presets" });
    await expect(list.getByText("Short clips")).toBeVisible();
    await expectNoHorizontalScroll(page);
    await list.getByRole("button", { name: "Delete Short clips" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();
    await expect(page.getByText("No presets yet")).toBeVisible();
  });

  test("names must be unique and options allowed", async ({ page }) => {
    await page.goto("/presets/new");
    await page.getByLabel("Name", { exact: true }).fill("Same");
    await page.getByRole("button", { name: "Save preset" }).click();
    await expect(page.getByRole("list", { name: "Presets" })).toBeVisible();

    await page.goto("/presets/new");
    await page.getByLabel("Name", { exact: true }).fill("Same");
    await page.getByRole("button", { name: "Save preset" }).click();
    await expect(page.getByText(/already exists/)).toBeVisible();

    await page.getByLabel("Name", { exact: true }).fill("Unsafe");
    await page.getByRole("button", { name: "Advanced options" }).click();
    await page.getByLabel("Extra yt-dlp options").fill("--exec ls");
    await page.getByRole("button", { name: "Save preset" }).click();
    await expect(page.getByText(/--exec isn't allowed/)).toBeVisible();
  });
});
