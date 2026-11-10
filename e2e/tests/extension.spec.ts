import {
  connect,
  expect,
  makeSendToken,
  openPopup,
  optionsPage,
  test,
} from "../fixtures/extension";

// Links the fake yt-dlp understands (see e2e/stub/fake_yt_dlp.py); nothing hits the network.
const VIDEO = "https://www.youtube.com/watch?v=extvideo";
const VIDEO_IN_PLAYLIST = "https://www.youtube.com/watch?v=extvideo&list=PLext";
const LIVE = "https://www.youtube.com/watch?v=extlive";

test.describe("browser extension", () => {
  test("opens its setup on install and checks the server and token", async ({
    extension,
    request,
    baseURL,
  }) => {
    const token = await makeSendToken(request);
    const page = await connect(extension, baseURL!, token);
    await expect(page.getByText(/Connected to yt-dlp-z \d/)).toBeVisible();
    await expect(page.getByRole("status")).toHaveText(/Saved/);
  });

  test("names what's wrong with the connection", async ({ extension, request, baseURL }) => {
    await makeSendToken(request);
    const page = await optionsPage(extension);
    await page.getByLabel("Server address").fill(baseURL!);
    await page.getByLabel("API token").fill("not-a-real-token");
    await page.getByRole("button", { name: "Test and save" }).click();
    await expect(page.getByText(/didn't accept the token/)).toBeVisible();

    await page.getByLabel("API token").fill("");
    await page.getByRole("button", { name: "Test and save" }).click();
    await expect(page.getByText("This server needs an API token.")).toBeVisible();

    await page.getByLabel("Server address").fill("127.0.0.1:9");
    await page.getByRole("button", { name: "Test and save" }).click();
    await expect(page.getByText(/Can't reach/)).toBeVisible();
  });

  test("the popup asks to set up first", async ({ extension }) => {
    const popup = await openPopup(extension, VIDEO);
    await expect(popup.getByText(/Connect the extension/)).toBeVisible();
    await expect(popup.getByRole("button", { name: "Set up" })).toBeVisible();
  });

  test("the popup checks a video and sends it", async ({ extension, request, baseURL }) => {
    await connect(extension, baseURL!, await makeSendToken(request));
    const popup = await openPopup(extension, VIDEO);
    await expect(popup.getByText("Video · 5:00 · Fake channel")).toBeVisible();
    await expect(popup.getByText("Fake video extvideo")).toBeVisible();
    await popup.getByRole("button", { name: "Download" }).click();
    await expect(popup.getByText("✓ Sent: Fake video extvideo")).toBeVisible();
    await expect(popup.getByRole("link", { name: "Open queue" })).toHaveAttribute(
      "href",
      `${baseURL}/queue`,
    );
    const jobs = await (await request.get("/api/jobs")).json();
    expect(JSON.stringify(jobs)).toContain("watch?v=extvideo");
  });

  test("the popup can send a whole playlist instead", async ({ extension, request, baseURL }) => {
    await connect(extension, baseURL!, await makeSendToken(request));
    const popup = await openPopup(extension, VIDEO_IN_PLAYLIST);
    await expect(popup.getByText("Video · 5:00 · Fake channel")).toBeVisible();
    await expect(popup.getByRole("button", { name: "Download", exact: true })).toBeVisible();
    await popup.getByRole("button", { name: "Whole playlist" }).click();
    await expect(popup.getByRole("button", { name: "Download 24 videos" })).toBeVisible();
    await popup.getByRole("button", { name: "Download 24 videos" }).click();
    await expect(popup.getByText(/✓ Sent/)).toBeVisible();
  });

  test("the popup records a live stream", async ({ extension, request, baseURL }) => {
    await connect(extension, baseURL!, await makeSendToken(request));
    const popup = await openPopup(extension, LIVE);
    await expect(popup.getByRole("button", { name: "Record" })).toBeVisible();
    await expect(popup.getByText(/Live now/)).toBeVisible();
  });

  test("checking links ahead can be switched on and stays on", async ({ extension }) => {
    const page = await optionsPage(extension);
    const toggle = page.getByLabel(/Check links ahead/);
    await expect(toggle).not.toBeChecked();
    await toggle.click();
    await expect(toggle).toBeChecked();
    await page.reload();
    await expect(page.getByLabel(/Check links ahead/)).toBeChecked();
  });
});
