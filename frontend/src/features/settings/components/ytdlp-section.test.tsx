import { screen } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

// The page polls a running update once a second.
const UPDATE_TIMEOUT = { timeout: 3000 };

describe("YtdlpSection", () => {
  it("shows the bundled version", async () => {
    installFakeApi(createFakeServer());
    renderApp("/settings");

    expect(
      await screen.findByText("Version 2026.10.26, bundled with the app."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Use bundled version" })).not.toBeInTheDocument();
  });

  it("updates yt-dlp and can go back to the bundled version", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/settings");

    await user.click(await screen.findByRole("button", { name: "Update now" }));

    expect(
      await screen.findByText("Updated yt-dlp to 2099.1.1.", {}, UPDATE_TIMEOUT),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Version 2099.1.1, updated \(the app came with 2026.10.26\)/),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Use bundled version" }));
    expect(
      await screen.findByText("Version 2026.10.26, bundled with the app."),
    ).toBeInTheDocument();
  });

  it("installs nightly builds when that channel is chosen", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/settings");

    await user.selectOptions(await screen.findByLabelText("Update channel"), "nightly");
    await user.click(screen.getByRole("button", { name: "Update now" }));

    expect(
      await screen.findByText("Updated yt-dlp to 2099.1.2.dev0.", {}, UPDATE_TIMEOUT),
    ).toBeInTheDocument();
    expect(server.ytdlp.channel).toBe("nightly");
  });

  it("explains a failed update", async () => {
    const server = createFakeServer();
    server.ytdlpUpdateFails = true;
    installFakeApi(server);
    const { user } = renderApp("/settings");

    await user.click(await screen.findByRole("button", { name: "Update now" }));

    expect(
      await screen.findByText("The update failed: no network", {}, UPDATE_TIMEOUT),
    ).toBeInTheDocument();
    expect(screen.getByText(/Version 2026.10.26, bundled/)).toBeInTheDocument();
  });
});

describe("YtdlpSection update checks", () => {
  it("says when a newer version is out, then that it is the newest", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/settings");

    await user.click(await screen.findByRole("button", { name: "Check for updates" }));
    expect(await screen.findByText("yt-dlp 2099.1.1 is available.")).toBeInTheDocument();
    expect(server.ytdlp.using_update).toBe(false);

    await user.click(screen.getByRole("button", { name: "Update now" }));
    expect(
      await screen.findByText(/The newest version \(checked/, {}, UPDATE_TIMEOUT),
    ).toBeInTheDocument();
  });

  it("turns automatic updates on", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/settings");

    await user.click(await screen.findByLabelText("Update automatically"));

    expect(await screen.findByLabelText("Update automatically")).toBeChecked();
    expect(server.ytdlp).toMatchObject({ auto_update: true, channel: "stable" });
  });
});

describe("YtdlpSection preferences", () => {
  it("puts the choice back when saving fails", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/settings");

    const checkbox = await screen.findByLabelText("Update automatically");
    server.failWith = 500;
    await user.click(checkbox);

    expect(await screen.findByText("Server error")).toBeInTheDocument();
    expect(screen.getByLabelText("Update automatically")).not.toBeChecked();
  });
});
