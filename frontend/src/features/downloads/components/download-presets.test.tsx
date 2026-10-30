import { screen } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { makeCookieFile, makePreset } from "@/test/fake-library";
import { CHECK_TIMEOUT } from "@/test/link-check";
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
});
