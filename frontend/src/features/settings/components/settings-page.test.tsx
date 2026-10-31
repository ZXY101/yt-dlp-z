import { screen } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

describe("SettingsPage", () => {
  it("saves the download folder and limit", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/settings");

    const folder = await screen.findByLabelText("Download folder");
    expect(folder).toHaveValue("/downloads");
    await user.clear(folder);
    await user.type(folder, "/media/videos ");
    const limit = screen.getByLabelText("Downloads at the same time");
    await user.clear(limit);
    await user.type(limit, "5");
    const recordings = screen.getByLabelText("Recordings at the same time");
    expect(recordings).toHaveValue("2");
    await user.clear(recordings);
    await user.type(recordings, "4");
    await user.click(screen.getByRole("button", { name: "Save settings" }));

    expect(await screen.findByText("Settings saved.")).toBeInTheDocument();
    expect(server.settings).toEqual({
      download_dir: "/media/videos",
      max_concurrent_downloads: 5,
      max_concurrent_recordings: 4,
      max_subscriptions: 5,
    });
  });

  it("raises the channel limit behind a rate-limit warning", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/settings");

    const channels = await screen.findByLabelText("Channels to watch");
    expect(screen.queryByText(/rate-limited or flagged/)).not.toBeInTheDocument();
    await user.clear(channels);
    await user.type(channels, "101");
    expect(screen.getByText(/rate-limited or flagged/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Save settings" }));
    expect(screen.getByText("Enter a whole number from 1 to 100.")).toBeVisible();
    expect(server.requests).not.toContain("PUT /api/settings");

    await user.clear(channels);
    await user.type(channels, "12");
    await user.click(screen.getByRole("button", { name: "Save settings" }));
    expect(await screen.findByText("Settings saved.")).toBeInTheDocument();
    expect(server.settings.max_subscriptions).toBe(12);
  });

  it.each(["0", "11", "2.5", "lots"])("rejects %s downloads at the same time", async (value) => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/settings");

    const limit = await screen.findByLabelText("Downloads at the same time");
    await user.clear(limit);
    await user.type(limit, value);
    await user.click(screen.getByRole("button", { name: "Save settings" }));
    expect(screen.getByText("Enter a whole number from 1 to 10.")).toBeInTheDocument();
    expect(server.requests).not.toContain("PUT /api/settings");
  });

  it("shows errors from the server", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/settings");

    const folder = await screen.findByLabelText("Download folder");
    await user.clear(folder);
    await user.type(folder, "relative");
    await user.click(screen.getByRole("button", { name: "Save settings" }));
    expect(await screen.findByText(/must be an absolute path/)).toBeInTheDocument();
  });

  it("shows load errors", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    server.failWith = 500;
    renderApp("/settings");
    expect(await screen.findByText("Server error")).toBeInTheDocument();
  });
});
