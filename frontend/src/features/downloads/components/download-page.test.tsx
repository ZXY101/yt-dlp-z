import { screen } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

describe("DownloadPage", () => {
  it("starts a download with the chosen options and opens the queue", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user, router } = renderApp("/");

    await user.type(await screen.findByLabelText("Link"), "https://example.com/watch/abc");
    await user.type(screen.getByLabelText("Save to"), "music");
    await user.selectOptions(screen.getByLabelText("Quality"), "audio-mp3");
    await user.click(screen.getByLabelText("Remove sponsor segments"));
    await user.click(screen.getByRole("button", { name: "Advanced options" }));
    await user.type(screen.getByLabelText("Extra yt-dlp options"), "--limit-rate 2M");
    await user.click(screen.getByRole("button", { name: "Download" }));

    expect(await screen.findByRole("heading", { name: "Queue" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/queue");
    expect(await screen.findByText("https://example.com/watch/abc")).toBeInTheDocument();
    expect(server.jobs[0]).toMatchObject({
      output_dir: "music",
      extra_args: "--limit-rate 2M",
      options: {
        "--extract-audio": true,
        "--audio-format": "mp3",
        "--sponsorblock-remove": ["sponsor"],
      },
    });
  });

  it("checks the link before sending anything", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/");

    await user.click(await screen.findByRole("button", { name: "Download" }));
    expect(screen.getByText(/Paste a link/)).toBeInTheDocument();

    await user.type(screen.getByLabelText("Link"), "youtube.com/watch");
    await user.click(screen.getByRole("button", { name: "Download" }));
    expect(screen.getByText(/full link/)).toBeInTheDocument();
    expect(server.requests).not.toContain("POST /api/jobs");
  });

  it("shows options the server refuses", async () => {
    installFakeApi(createFakeServer());
    const { user, router } = renderApp("/");

    await user.type(await screen.findByLabelText("Link"), "https://example.com/v");
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

  it("downloads just the video from a playlist link unless asked for the whole playlist", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/");

    await user.type(
      await screen.findByLabelText("Link"),
      "https://www.youtube.com/watch?v=abc&list=PL1",
    );
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

    await user.type(await screen.findByLabelText("Link"), "https://youtu.be/abc?list=PL1");
    await user.click(screen.getByLabelText("The whole playlist"));
    await user.click(screen.getByRole("button", { name: "Download" }));
    await screen.findByRole("heading", { name: "Queue" });
    expect(server.jobs[0]?.options).toMatchObject({ "--yes-playlist": true });
    expect(server.jobs[0]?.options).not.toHaveProperty("--no-playlist");
  });

  it("warns that playlist and channel links download every video", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/");

    const link = await screen.findByLabelText("Link");
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    await user.type(link, "https://www.youtube.com/playlist?list=PL1");
    expect(screen.getByRole("status")).toHaveTextContent(/every video in it/);
    await user.clear(link);
    await user.type(link, "https://www.youtube.com/@someone/videos");
    expect(screen.getByRole("status")).toHaveTextContent(/every video on it/);
    expect(screen.queryByLabelText("Just this video")).not.toBeInTheDocument();
  });
});
