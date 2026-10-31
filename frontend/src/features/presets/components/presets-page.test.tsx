import { screen, within } from "@testing-library/react";

import { DEFAULT_RECORDING } from "@/features/presets";
import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { makeCookieFile, makePreset } from "@/test/fake-library";
import { makeProxy } from "@/test/fake-proxies";
import { renderApp } from "@/test/render";

describe("Presets", () => {
  it("explains presets when there are none, and links to the editor", async () => {
    installFakeApi(createFakeServer());
    const { user, router } = renderApp("/presets");
    await user.click(await screen.findByRole("link", { name: /No presets yet/ }));
    expect(router.state.location.pathname).toBe("/presets/new");
  });

  it("creates a preset from the editor", async () => {
    const server = createFakeServer();
    server.cookieFiles = [makeCookieFile({ id: 4, name: "YouTube" })];
    installFakeApi(server);
    const { user, router } = renderApp("/presets");

    await user.click(await screen.findByRole("link", { name: "New preset" }));
    await user.type(await screen.findByLabelText("Name"), "Podcasts");
    await user.click(screen.getByLabelText("Use by default"));
    await user.selectOptions(screen.getByLabelText("Quality"), "audio");
    await user.type(screen.getByLabelText("Save to"), "podcasts");
    await user.selectOptions(await screen.findByLabelText("Cookies"), "4");
    await user.selectOptions(screen.getByLabelText("Media server"), "season");
    await user.click(screen.getByRole("button", { name: "Save preset" }));

    const list = await screen.findByRole("list", { name: "Presets" });
    expect(router.state.location.pathname).toBe("/presets");
    expect(within(list).getByText("Podcasts")).toBeInTheDocument();
    expect(within(list).getByText("Default")).toBeInTheDocument();
    const summary = /Saves to podcasts · 3 options · with cookies · for media servers/;
    expect(within(list).getByText(summary)).toBeVisible();
    expect(server.presets[0]).toMatchObject({
      name: "Podcasts",
      is_default: true,
      output_dir: "podcasts",
      cookie_id: 4,
      media_layout: "season",
      options: { "--extract-audio": true, "--embed-metadata": true, "--embed-thumbnail": true },
    });
  });

  it("sends a preset's downloads through the proxy pool", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/presets/new");

    await user.type(await screen.findByLabelText("Name"), "Hidden");
    // No proxies yet: the choice stays hidden.
    expect(screen.queryByLabelText("Proxy")).not.toBeInTheDocument();
    server.proxies = [makeProxy()];
    await user.click(screen.getByRole("button", { name: "Save preset" }));
    await screen.findByRole("list", { name: "Presets" });

    await user.click(screen.getByRole("link", { name: "Edit Hidden" }));
    await user.selectOptions(await screen.findByLabelText("Proxy"), "sticky");
    await user.click(screen.getByRole("button", { name: "Save preset" }));
    expect(await screen.findByText(/through proxies/)).toBeVisible();
    expect(server.presets[0]?.proxy_mode).toBe("sticky");

    server.proxies = [];
    await user.click(screen.getByRole("link", { name: "Edit Hidden" }));
    expect(await screen.findByText(/There are no proxies in Settings/)).toBeVisible();
  });

  it("edits an existing preset", async () => {
    const server = createFakeServer();
    server.presets = [makePreset({ id: 3, name: "Music", extra_args: "--limit-rate 1M" })];
    installFakeApi(server);
    const { user } = renderApp("/presets");

    expect(await screen.findByText(/Default folder · 0 options · extra options/)).toBeVisible();
    await user.click(screen.getByRole("link", { name: "Edit Music" }));
    const name = await screen.findByLabelText("Name");
    expect(name).toHaveValue("Music");
    await user.clear(name);
    await user.type(name, "Songs");
    await user.click(screen.getByRole("button", { name: "Save preset" }));

    expect(await screen.findByText("Songs")).toBeInTheDocument();
    expect(server.presets[0]).toMatchObject({
      id: 3,
      name: "Songs",
      extra_args: "--limit-rate 1M",
    });
  });

  it("asks before deleting a preset", async () => {
    const server = createFakeServer();
    server.presets = [makePreset({ name: "Music" })];
    installFakeApi(server);
    const { user } = renderApp("/presets");

    await user.click(await screen.findByRole("button", { name: "Delete Music" }));
    await user.click(screen.getByRole("button", { name: "Keep it" }));
    expect(server.presets).toHaveLength(1);

    await user.click(screen.getByRole("button", { name: "Delete Music" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Delete" }));
    expect(await screen.findByText("No presets yet")).toBeInTheDocument();
  });

  it("checks the name and shows server errors", async () => {
    const server = createFakeServer();
    server.presets = [makePreset({ name: "Music" })];
    installFakeApi(server);
    const { user } = renderApp("/presets/new");

    await user.click(await screen.findByRole("button", { name: "Save preset" }));
    expect(screen.getByText("Give the preset a name.")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Name"), "Music");
    await user.click(screen.getByRole("button", { name: "Save preset" }));
    expect(await screen.findByText(/already exists/)).toBeInTheDocument();
  });

  it("says when a preset doesn't exist", async () => {
    installFakeApi(createFakeServer());
    renderApp("/presets/99");
    expect(await screen.findByText("This preset doesn't exist any more.")).toBeInTheDocument();
  });

  it("shows load errors", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    server.failWith = 500;
    renderApp("/presets");
    expect(await screen.findByText("Server error")).toBeInTheDocument();
  });

  it("records live streams with a live-stream preset; empty turns a limit off", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/presets/new");

    await user.type(await screen.findByLabelText("Name"), "Concerts");
    expect(screen.queryByLabelText("New file every (hours)")).not.toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Use for"), "live");
    await user.click(screen.getByLabelText("Use by default for live streams"));
    const part = screen.getByLabelText("New file every (hours)");
    expect(part).toHaveValue("6");
    expect(screen.getByLabelText("Stop after (hours)")).toHaveValue("");
    await user.clear(part);
    await user.type(screen.getByLabelText("Stop after (hours)"), "200");
    await user.click(screen.getByRole("button", { name: "Save preset" }));
    expect(
      screen.getByText("Enter a whole number from 1 to 168, or leave it empty."),
    ).toBeVisible();
    expect(server.presets).toEqual([]);

    const max = screen.getByLabelText("Stop after (hours)");
    await user.clear(max);
    await user.type(max, "12");
    await user.click(screen.getByRole("button", { name: "Save preset" }));
    const list = await screen.findByRole("list", { name: "Presets" });
    expect(within(list).getByText("Live streams")).toBeInTheDocument();
    expect(within(list).getByText(/one file · stops after 12 hours/)).toBeVisible();
    expect(server.presets[0]).toMatchObject({
      kind: "live",
      is_default: true,
      recording: { part_hours: null, max_hours: 12, from_start_max_hours: 6 },
    });
  });

  it("can record the first hours of streams found after running long", async () => {
    const server = createFakeServer();
    server.presets = [makePreset({ kind: "live", name: "Streams", recording: DEFAULT_RECORDING })];
    installFakeApi(server);
    const { user } = renderApp("/presets/1");

    const limit = await screen.findByLabelText(
      "Record from the start, unless live longer than (hours)",
    );
    const choice = screen.getByRole("group", {
      name: "Streams live longer than 6 hours when found",
    });
    expect(within(choice).getByRole("radio", { name: "Record from now" })).toBeChecked();
    await user.clear(limit);
    await user.type(limit, "1");
    await user.click(screen.getByRole("radio", { name: "Record their first 1 hour" }));
    await user.click(screen.getByRole("button", { name: "Save preset" }));
    await screen.findByRole("list", { name: "Presets" });
    expect(server.presets[0]?.recording).toMatchObject({
      from_start_max_hours: 1,
      long_streams: "first_hours",
    });
  });

  it("drops the recording settings when a preset stops being for live streams", async () => {
    const server = createFakeServer();
    server.presets = [makePreset({ kind: "live", recording: DEFAULT_RECORDING })];
    installFakeApi(server);
    const { user } = renderApp("/presets/1");

    await user.selectOptions(await screen.findByLabelText("Use for"), "playlist");
    expect(screen.getByLabelText("Use by default for playlists and channels")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Save preset" }));
    await screen.findByRole("list", { name: "Presets" });
    expect(server.presets[0]).toMatchObject({ kind: "playlist", recording: null });
  });
});
