import { screen, within } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { makeCookieFile, makePreset } from "@/test/fake-library";
import { renderApp } from "@/test/render";

describe("Presets", () => {
  it("explains presets when there are none", async () => {
    installFakeApi(createFakeServer());
    renderApp("/presets");
    expect(await screen.findByText("No presets yet")).toBeInTheDocument();
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
    await user.click(screen.getByRole("button", { name: "Save preset" }));

    const list = await screen.findByRole("list", { name: "Presets" });
    expect(router.state.location.pathname).toBe("/presets");
    expect(within(list).getByText("Podcasts")).toBeInTheDocument();
    expect(within(list).getByText("Default")).toBeInTheDocument();
    expect(within(list).getByText(/Saves to podcasts · 3 options · with cookies/)).toBeVisible();
    expect(server.presets[0]).toMatchObject({
      name: "Podcasts",
      is_default: true,
      output_dir: "podcasts",
      cookie_id: 4,
      options: { "--extract-audio": true, "--embed-metadata": true, "--embed-thumbnail": true },
    });
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
});
