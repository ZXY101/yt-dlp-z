import { screen, within } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { CHECK_TIMEOUT, enterCheckedLink } from "@/test/link-check";
import { renderApp } from "@/test/render";

describe("DownloadPage", () => {
  it("starts a download with the chosen options and opens the queue", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user, router } = renderApp("/");

    await enterCheckedLink(user, "https://example.com/watch/abc");
    await user.type(screen.getByLabelText("Save to"), "music");
    await user.selectOptions(screen.getByLabelText("Quality"), "audio-mp3");
    await user.click(screen.getByLabelText("Remove sponsor segments"));
    await user.click(screen.getByRole("button", { name: "Advanced options" }));
    await user.type(screen.getByLabelText("Extra yt-dlp options"), "--limit-rate 2M");
    await user.click(screen.getByRole("button", { name: "Download" }));

    expect(await screen.findByRole("heading", { name: "Queue" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/queue");
    expect(await screen.findByText("Fake video")).toBeInTheDocument();
    expect(server.jobs[0]).toMatchObject({
      kind: "download",
      title: "Fake video",
      output_dir: "music",
      extra_args: "--limit-rate 2M",
      options: {
        "--extract-audio": true,
        "--audio-format": "mp3",
        "--sponsorblock-remove": ["sponsor"],
      },
    });
  });

  it("can't download until the link has been checked", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/");

    const download = await screen.findByRole("button", { name: "Download" });
    expect(download).toBeDisabled();
    await user.type(screen.getByLabelText("Link"), "youtube.com/watch");
    expect(await screen.findByText(/full link/, {}, CHECK_TIMEOUT)).toBeInTheDocument();
    expect(download).toBeDisabled();
    expect(server.requests).not.toContain("POST /api/media/probe");
  });

  it("shows the media it found", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/");

    await user.type(await screen.findByLabelText("Link"), "https://example.com/watch/abc");
    expect(await screen.findByText("Checking link…")).toBeInTheDocument();
    const details = await screen.findByLabelText("Media details", {}, CHECK_TIMEOUT);
    expect(details).toHaveTextContent("Fake video");
    expect(details).toHaveTextContent("Fake channel · youtube.com · 5:00");
    expect(screen.getByRole("button", { name: "Download" })).toBeEnabled();
  });

  it("checks a pasted link without waiting", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/");

    await user.click(await screen.findByLabelText("Link"));
    await user.paste("https://example.com/watch/abc");

    // Typed links wait 0.6 s for typing to pause; a paste is checked at once.
    expect(await screen.findByLabelText("Media details", {}, { timeout: 400 })).toBeInTheDocument();
  });

  it("explains links yt-dlp can't open", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/");

    await user.type(await screen.findByLabelText("Link"), "https://example.com/watch/broken");
    expect(
      await screen.findByText(/This video is unavailable/, {}, CHECK_TIMEOUT),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download" })).toBeDisabled();
  });

  it("shows options the server refuses", async () => {
    installFakeApi(createFakeServer());
    const { user, router } = renderApp("/");

    await enterCheckedLink(user, "https://example.com/v");
    await user.click(screen.getByRole("button", { name: "Advanced options" }));
    await user.type(screen.getByLabelText("Extra yt-dlp options"), "--exec 'rm -rf /'");
    await user.click(screen.getByRole("button", { name: "Download" }));

    expect(await screen.findByText(/--exec isn't allowed/)).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/");
  });

  it("keeps advanced options hidden until asked", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/");

    const toggle = await screen.findByRole("button", { name: "Advanced options" });
    expect(screen.queryByLabelText("File name template")).not.toBeVisible();
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByLabelText("File name template")).toBeVisible();
  });

  it("saves into channel folders with a chosen file name", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/");

    await enterCheckedLink(user, "https://example.com/v");
    await user.selectOptions(screen.getByLabelText("Sub-folders"), "channel");
    await user.click(screen.getByRole("button", { name: "Advanced options" }));
    expect(screen.getByText(/used inside the sub-folders/)).toBeVisible();
    await user.selectOptions(screen.getByLabelText("File name"), "dated");
    expect(screen.getByText(/Not used: File name above/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Download" }));
    await screen.findByRole("heading", { name: "Queue" });
    expect(server.jobs[0]).toMatchObject({
      folders: "channel",
      file_name: "dated",
      media_files: false,
    });
  });

  it("downloads just the video from a playlist link unless asked for the whole playlist", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/");

    const details = await enterCheckedLink(user, "https://www.youtube.com/watch?v=abc&list=PL1");
    expect(details).toHaveTextContent("Fake video");
    expect(screen.getByLabelText("Just this video")).toBeChecked();
    await user.click(screen.getByRole("button", { name: "Download" }));
    await screen.findByRole("heading", { name: "Queue" });
    expect(server.jobs[0]?.options).toMatchObject({ "--no-playlist": true });
    expect(server.jobs[0]?.options).not.toHaveProperty("--yes-playlist");
  });

  it("downloads the whole playlist when chosen", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/");

    await enterCheckedLink(user, "https://youtu.be/abc?list=PL1");
    await user.click(screen.getByLabelText("The whole playlist"));
    const details = await screen.findByLabelText("Media details", {}, CHECK_TIMEOUT);
    expect(await within(details).findByText(/Playlist · 24 videos/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Download" }));
    await screen.findByRole("heading", { name: "Queue" });
    expect(server.jobs[0]?.options).toMatchObject({ "--yes-playlist": true });
    expect(server.jobs[0]?.options).not.toHaveProperty("--no-playlist");
  });

  it("warns that playlist and channel links download every video", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/");

    await enterCheckedLink(user, "https://www.youtube.com/playlist?list=PL1");
    expect(screen.getByText(/all 24 videos in it will be downloaded/)).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Link"));
    await enterCheckedLink(user, "https://www.youtube.com/@someone");
    expect(screen.getByText(/every video, Short and stream/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Just this video")).not.toBeInTheDocument();
  });

  it("records a live stream, from now when chosen", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/");

    const details = await enterCheckedLink(user, "https://www.youtube.com/watch?v=live1");
    expect(details).toHaveTextContent("Live now");
    expect(screen.getByText("This stream has been live for 1 h 0 min.")).toBeVisible();
    expect(screen.getByLabelText("From the start")).toBeChecked();
    await user.click(screen.getByLabelText("From now"));
    const stopAfter = screen.getByLabelText("Stop after (hours)");
    await user.type(stopAfter, "2");
    await user.click(screen.getByRole("button", { name: "Record" }));

    await screen.findByRole("heading", { name: "Queue" });
    expect(server.jobs[0]).toMatchObject({
      kind: "live",
      record_from_start: false,
      part_seconds: 6 * 3600,
      max_seconds: 2 * 3600,
    });
  });

  it("checks the recording hours before recording", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/");

    await enterCheckedLink(user, "https://www.youtube.com/watch?v=live1");
    await user.type(screen.getByLabelText("Stop after (hours)"), "0");
    await user.click(screen.getByRole("button", { name: "Record" }));
    expect(screen.getByText(/Enter a whole number from 1 to 168/)).toBeVisible();
    expect(server.jobs).toEqual([]);
  });

  it("suggests recording long-running streams from now", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/");

    await enterCheckedLink(user, "https://www.youtube.com/watch?v=live-old1");
    expect(screen.getByLabelText("From now")).toBeChecked();
  });

  it("schedules a recording for an upcoming stream", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/");

    await enterCheckedLink(user, "https://www.youtube.com/watch?v=upcoming1");
    expect(screen.getByText(/starts when the stream does/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Schedule recording" }));

    await screen.findByRole("heading", { name: "Queue" });
    expect(server.jobs[0]).toMatchObject({
      kind: "live",
      status: "scheduled",
      scheduled_at: "2100-01-01T00:00:00+00:00",
      record_from_start: true,
    });
  });
});
