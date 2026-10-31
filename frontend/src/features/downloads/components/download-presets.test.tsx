import { screen, within } from "@testing-library/react";

import { DEFAULT_RECORDING } from "@/features/presets";
import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { makeCookieFile, makePreset } from "@/test/fake-library";
import { CHECK_TIMEOUT, enterCheckedLink } from "@/test/link-check";
import { renderApp } from "@/test/render";

function serverWithPresets() {
  const server = createFakeServer();
  server.presets = [
    makePreset({
      id: 1,
      name: "Music",
      is_default: true,
      options: { "--extract-audio": true, "--audio-format": "mp3" },
      output_dir: "music",
    }),
    makePreset({ id: 2, name: "Clips", options: { "--format-sort": ["res:720"] } }),
  ];
  server.cookieFiles = [makeCookieFile({ id: 7, name: "YouTube" })];
  return server;
}

describe("DownloadPage presets and cookies", () => {
  it("starts with the default preset and can switch to another", async () => {
    const server = serverWithPresets();
    installFakeApi(server);
    const { user } = renderApp("/");

    const preset = await screen.findByLabelText("Preset");
    expect(preset).toHaveValue("1");
    expect(screen.getByLabelText("Quality")).toHaveValue("audio-mp3");
    expect(screen.getByLabelText("Save to")).toHaveValue("music");

    await user.selectOptions(preset, "2");
    expect(screen.getByLabelText("Quality")).toHaveValue("720p");
    expect(screen.getByLabelText("Save to")).toHaveValue("");

    await user.selectOptions(preset, "");
    expect(screen.getByLabelText("Quality")).toHaveValue("best");
    expect(screen.getByLabelText("Embed thumbnail and metadata")).toBeChecked();
  });

  it("sends the chosen cookies with the download", async () => {
    const server = serverWithPresets();
    installFakeApi(server);
    const { user } = renderApp("/");

    await user.type(await screen.findByLabelText("Link"), "https://example.com/members");
    expect(await screen.findByText(/channel members only/, {}, CHECK_TIMEOUT)).toBeInTheDocument();
    await user.selectOptions(await screen.findByLabelText("Cookies"), "7");
    await screen.findByLabelText("Media details", {}, CHECK_TIMEOUT);
    await user.click(screen.getByRole("button", { name: "Download" }));

    await screen.findByRole("heading", { name: "Queue" });
    expect(server.jobs[0]).toMatchObject({ cookie_id: 7, output_dir: "music" });
  });

  it("hides the preset and cookies pickers until there is something to pick", async () => {
    installFakeApi(createFakeServer());
    renderApp("/");
    await screen.findByLabelText("Link");
    expect(screen.queryByLabelText("Preset")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Cookies")).not.toBeInTheDocument();
  });

  it("shows options set another way as a custom quality", async () => {
    const server = createFakeServer();
    server.presets = [makePreset({ is_default: true, options: { "--format-sort": ["res:480"] } })];
    installFakeApi(server);
    renderApp("/");
    expect(await screen.findByDisplayValue("Custom (see all options)")).toBeInTheDocument();
  });

  it("picks the default preset for the kind of link it checked", async () => {
    const server = serverWithPresets();
    server.presets.push(
      makePreset({ id: 3, name: "Lists", kind: "playlist", is_default: true, output_dir: "lists" }),
      makePreset({
        id: 4,
        name: "Streams",
        kind: "live",
        is_default: true,
        output_dir: "streams",
        recording: { ...DEFAULT_RECORDING, part_hours: 2, max_hours: 8 },
      }),
    );
    installFakeApi(server);
    const { user } = renderApp("/");

    expect(await screen.findByLabelText("Preset")).toHaveValue("1");
    await enterCheckedLink(user, "https://www.youtube.com/playlist?list=PL1");
    expect(screen.getByLabelText("Preset")).toHaveValue("3");
    const names = within(screen.getByLabelText("Preset"))
      .getAllByRole("option")
      .map((option) => option.textContent);
    expect(names.slice(0, 2)).toEqual(["None", "Lists (playlists and channels)"]);

    await user.clear(screen.getByLabelText("Link"));
    await enterCheckedLink(user, "https://www.youtube.com/watch?v=live1");
    expect(screen.getByLabelText("Preset")).toHaveValue("4");
    expect(screen.getByLabelText("Save to")).toHaveValue("streams");
    expect(screen.getByLabelText("New file every (hours)")).toHaveValue("2");
    expect(screen.getByLabelText("Stop after (hours)")).toHaveValue("8");

    // A preset without recording settings records with the default live-stream preset's.
    await user.selectOptions(screen.getByLabelText("Preset"), "2");
    expect(screen.getByLabelText("New file every (hours)")).toHaveValue("2");
  });

  it("records the first hours of long-running streams when the preset says so", async () => {
    const server = createFakeServer();
    const recording = { ...DEFAULT_RECORDING, long_streams: "first_hours" as const };
    server.presets = [makePreset({ kind: "live", is_default: true, recording })];
    installFakeApi(server);
    const { user } = renderApp("/");

    await screen.findByLabelText("Preset");
    await enterCheckedLink(user, "https://www.youtube.com/watch?v=live-old1");
    expect(screen.getByLabelText("From the start")).toBeChecked();
    expect(screen.getByLabelText("Stop after (hours)")).toHaveValue("6");
  });
});
