import {
  completeSetupViaApi,
  expect,
  expectNoHorizontalScroll,
  setFeed,
  signIn,
  test,
} from "../fixtures/app";

// The fake yt-dlp resolves @demo to this channel id (see stub/fake_yt_dlp.py).
const DEMO_ID = "UCdemo";

async function addChannel(page: import("@playwright/test").Page, channel: string, backfill = "0") {
  await page.goto("/subscriptions/new");
  await page.getByLabel("Channel", { exact: true }).fill(channel);
  await page.getByLabel("Download recent uploads now").fill(backfill);
  await page.getByRole("button", { name: "Save subscription" }).click();
}

test.describe("subscriptions", () => {
  test.beforeEach(async ({ page, request }) => {
    await completeSetupViaApi(request);
    await signIn(page);
    await expect(page.getByRole("heading", { name: "Download", exact: true })).toBeVisible();
  });

  test("a new channel downloads its recent uploads and filters later ones", async ({
    page,
    request,
  }) => {
    await setFeed(request, DEMO_ID, ["plain1", "short1", "older"]);
    await page.goto("/subscriptions");
    await page.getByRole("link", { name: /No channels watched yet/ }).click();
    await page.getByLabel("Channel", { exact: true }).fill("@demo");
    await page.getByLabel("Download recent uploads now").fill("2");
    await expectNoHorizontalScroll(page);
    await page.getByRole("button", { name: "Save subscription" }).click();

    const list = page.getByRole("list", { name: "Subscriptions" });
    await expect(list.getByText("Fake demo")).toBeVisible();
    await expect(list.getByText(/Checked just now · every 10 min/)).toBeVisible();
    await expectNoHorizontalScroll(page);

    await page.getByRole("link", { name: "Edit Fake demo" }).click();
    const videos = page.getByRole("list", { name: "Recent videos" });
    await expect(videos.getByText("Fake video plain1")).toBeVisible();
    await expect(videos.getByText("It's a Short")).toBeVisible();
    await expect(videos.getByText("Uploaded before you subscribed")).toBeVisible();
    await expectNoHorizontalScroll(page);

    await page.goto("/queue");
    const finished = page.getByRole("list", { name: "Finished" });
    await expect(finished.getByText("Fake video plain1", { exact: true })).toBeVisible();

    // Tapping the channel shows what it downloaded, with the queue's actions.
    await page.goto("/subscriptions");
    await page.getByRole("button", { name: /^Fake demo/, expanded: false }).click();
    const downloads = page.getByRole("list", { name: "Downloads from Fake demo" });
    await expect(downloads.getByText("Fake video plain1", { exact: true })).toBeVisible();
    await expect(downloads.getByText(/Saved to /)).toBeVisible();
    await expect(downloads.getByRole("button", { name: /Log/ })).toBeVisible();
    await expectNoHorizontalScroll(page);

    await setFeed(request, DEMO_ID, ["upcoming1", "plain1", "short1", "older"]);
    await page.goto("/subscriptions");
    await page.getByRole("button", { name: "Check Fake demo now" }).click();
    await page.getByRole("link", { name: "Edit Fake demo" }).click();
    // Streams aren't wanted by default, so the upcoming stream is skipped.
    await expect(videos.getByText("It's a live stream or premiere")).toBeVisible();
  });

  test("filters and settings can be edited, paused and deleted", async ({ page, request }) => {
    await setFeed(request, DEMO_ID, []);
    await addChannel(page, "@demo");
    await page.getByRole("link", { name: "Edit Fake demo" }).click();
    await page.getByLabel("Live streams and premieres").check();
    await page.getByLabel("Check every (minutes)").fill("30");
    await page.getByLabel("Skip titles matching").fill("trailer");
    await page.getByRole("button", { name: "Save subscription" }).click();
    await expect(page.getByText(/every 30 min/)).toBeVisible();

    await page.reload();
    await page.getByRole("link", { name: "Edit Fake demo" }).click();
    await expect(page.getByLabel("Live streams and premieres")).toBeChecked();
    await expect(page.getByLabel("Skip titles matching")).toHaveValue("trailer");

    await setFeed(request, DEMO_ID, ["upcoming1"]);
    await page.goto("/subscriptions");
    await page.getByRole("button", { name: "Check Fake demo now" }).click();
    await page.getByRole("link", { name: "Edit Fake demo" }).click();
    await expect(
      page
        .getByRole("list", { name: "Recent videos" })
        .getByText("Recording scheduled", { exact: true }),
    ).toBeVisible();

    await page.goto("/subscriptions");
    await page.getByRole("button", { name: "Pause Fake demo" }).click();
    await expect(page.getByText("Paused")).toBeVisible();
    await page.reload();
    await expect(page.getByRole("button", { name: "Resume Fake demo" })).toBeVisible();

    await page.getByRole("button", { name: "Delete Fake demo" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();
    await expect(page.getByText("No channels watched yet")).toBeVisible();
  });

  test("problems are explained", async ({ page }) => {
    await addChannel(page, "@failing");
    await expect(page.getByText(/This channel does not exist/)).toBeVisible();

    await page.getByLabel("Channel", { exact: true }).fill("https://example.com/@demo");
    await page.getByRole("button", { name: "Save subscription" }).click();
    await expect(page.getByText("Enter a YouTube channel URL or @handle")).toBeVisible();

    // No feed is served and the fake yt-dlp can't list its videos tab: the check fails.
    await page.getByLabel("Channel", { exact: true }).fill("@broken");
    await page.getByRole("button", { name: "Save subscription" }).click();
    await expect(
      page.getByText(/Couldn't load the channel feed.*videos tab failed too/),
    ).toBeVisible();
    await expect(page.getByText("Not checked yet")).toBeVisible();
  });

  test("the channel limit is enforced and can be raised", async ({ page, request }) => {
    await setFeed(request, DEMO_ID, []);
    await page.goto("/settings");
    await page.getByLabel("Channels to watch").fill("1");
    await page.getByRole("button", { name: "Save settings" }).click();
    await expect(page.getByText("Settings saved.")).toBeVisible();

    await addChannel(page, "@demo");
    await expect(page.getByText("Fake demo")).toBeVisible();
    await addChannel(page, "@other");
    await expect(page.getByText(/watching 1 of 1 channels/)).toBeVisible();

    await page.goto("/settings");
    await page.getByLabel("Channels to watch").fill("8");
    await expect(page.getByText(/rate-limited or flagged/)).toBeVisible();
    await expectNoHorizontalScroll(page);
    await page.getByRole("button", { name: "Save settings" }).click();
    await expect(page.getByText("Settings saved.")).toBeVisible();
    await addChannel(page, "@other");
    await expect(page.getByText("Fake other")).toBeVisible();
  });
});
