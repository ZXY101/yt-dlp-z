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
    await page.goto("/presets/new");
    await page.getByLabel("Name", { exact: true }).fill("Audio");
    await page.getByLabel("Use by default").check();
    await page.getByLabel("Quality").selectOption("audio-mp3");
    await page.getByLabel("Save to").fill("audio");
    await expectNoHorizontalScroll(page);
    await page.getByRole("button", { name: "Save preset" }).click();

    const audio = page.getByRole("listitem").filter({ hasText: "Audio" });
    await expect(audio.getByText("Default")).toBeVisible();
    await page.reload();
    await expect(audio.getByText(/Saves to audio · 4 options/)).toBeVisible();

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

  test("a media-server preset saves videos as episodes of a show", async ({ page }) => {
    await page.goto("/presets/new");
    await page.getByLabel("Name", { exact: true }).fill("Jellyfin");
    await page.getByLabel("Media server").selectOption("season");
    await page.getByRole("button", { name: "Save preset" }).click();
    const preset = page.getByRole("listitem").filter({ hasText: "Jellyfin" });
    await expect(preset.getByText(/for media servers/)).toBeVisible();

    await page.goto("/");
    await page.getByLabel("Preset").selectOption({ label: "Jellyfin" });
    await expect(page.getByLabel("Media server")).toHaveValue("season");
    await page.getByLabel("Link").fill("https://example.com/watch/show");
    await page.getByRole("button", { name: "Download" }).click();

    const finished = page.getByRole("list", { name: "Finished" });
    const episode = /Saved to .*\/Fake channel\/Season 2026\/Fake channel - S2026E1001 - /;
    await expect(finished.getByText(episode)).toBeVisible();
    await finished.getByRole("button", { name: "Log" }).click();
    await expect(page.getByRole("dialog").getByText(/--write-thumbnail/)).toBeVisible();
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
    await expect(list.getByText("Short clips")).toBeHidden();
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

  test("a live-stream preset decides how streams are recorded", async ({ page }) => {
    // The test reset removes the "Live streams" preset a fresh install starts with.
    await page.goto("/presets/new");
    await page.getByLabel("Name", { exact: true }).fill("Live streams");
    await page.getByLabel("Use for").selectOption("live");
    await page.getByLabel("Use by default for live streams").check();
    await page.getByLabel("New file every (hours)").fill("");
    await page.getByLabel("Stop after (hours)").fill("12");
    await page.getByRole("radio", { name: "Record their first 6 hours" }).check();
    await expectNoHorizontalScroll(page);
    await page.getByRole("button", { name: "Save preset" }).click();
    const live = page.getByRole("listitem").filter({ hasText: "Live streams" });
    await expect(live.getByText(/one file · stops after 12 hours/)).toBeVisible();

    await page.getByRole("link", { name: "Edit Live streams" }).click();
    await expect(page.getByLabel("Stop after (hours)")).toHaveValue("12");
    await expect(page.getByRole("radio", { name: "Record their first 6 hours" })).toBeChecked();

    await page.goto("/");
    await page.getByLabel("Link").fill("https://www.youtube.com/watch?v=live-preset");
    await expect(page.getByLabel("Media details")).toContainText("Live now");
    await expect(page.getByLabel("Preset")).toHaveValue(/\d+/);
    await expect(page.getByLabel("New file every (hours)")).toHaveValue("");
    await expect(page.getByLabel("Stop after (hours)")).toHaveValue("12");
    await page.getByLabel("Stop after (hours)").fill("2");
    await page.getByRole("button", { name: "Record" }).click();

    await expect(page).toHaveURL(/\/queue$/);
    await expect(page.getByText("Recording", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Cancel Fake video live-preset" }).click();
  });
});
