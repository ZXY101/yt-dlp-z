import { screen, within } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { makeCookieFile, makePreset } from "@/test/fake-library";
import { makeSubscription, makeVideo } from "@/test/fake-subscriptions";
import { renderApp } from "@/test/render";

describe("Subscriptions", () => {
  it("explains subscriptions when there are none, and links to adding one", async () => {
    installFakeApi(createFakeServer());
    const { user, router } = renderApp("/subscriptions");
    await user.click(await screen.findByRole("link", { name: /No channels watched yet/ }));
    expect(router.state.location.pathname).toBe("/subscriptions/new");
  });

  it("adds a channel with a preset, cookies and filters", async () => {
    const server = createFakeServer();
    server.presets = [makePreset({ id: 2, name: "Audio" })];
    server.cookieFiles = [makeCookieFile({ id: 4, name: "Member" })];
    installFakeApi(server);
    const { user, router } = renderApp("/subscriptions");

    await user.click(await screen.findByRole("link", { name: "Watch a channel" }));
    await user.type(await screen.findByLabelText("Channel"), "@demo");
    const backfill = screen.getByLabelText("Download recent uploads now");
    await user.clear(backfill);
    await user.type(backfill, "3");
    await user.selectOptions(await screen.findByLabelText("Preset"), "2");
    await user.selectOptions(await screen.findByLabelText("Cookies"), "4");
    await user.click(screen.getByLabelText("Shorts"));
    await user.type(screen.getByLabelText("Skip titles matching"), "trailer");
    await user.type(screen.getByLabelText("Longest (minutes)"), "1.5");
    await user.click(screen.getByLabelText("Include members-only videos"));
    await user.click(screen.getByRole("button", { name: "Save subscription" }));

    const list = await screen.findByRole("list", { name: "Subscriptions" });
    expect(router.state.location.pathname).toBe("/subscriptions");
    expect(within(list).getByText("Fake demo")).toBeInTheDocument();
    expect(server.subscriptions[0]).toMatchObject({
      backfill: 3,
      preset_id: 2,
      cookie_id: 4,
      filters: {
        content_types: ["video", "short"],
        title_exclude: "trailer",
        max_duration: 90,
        min_duration: null,
        include_members_only: true,
      },
    });
  });

  it("checks the form before sending it", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/subscriptions/new");

    const poll = await screen.findByLabelText("Check every (minutes)");
    await user.clear(poll);
    await user.type(poll, "1");
    await user.click(screen.getByLabelText("Videos"));
    await user.type(screen.getByLabelText("Shortest (minutes)"), "x");
    await user.click(screen.getByRole("button", { name: "Save subscription" }));

    expect(await screen.findByText("Enter a channel URL or @handle.")).toBeVisible();
    expect(screen.getByText("Enter a whole number from 5 to 10080.")).toBeVisible();
    expect(screen.getByText("Pick at least one.")).toBeVisible();
    expect(screen.getByText("Enter a number of minutes.")).toBeVisible();
  });

  it("shows the server's reason when a channel can't be added", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/subscriptions/new");
    await user.type(await screen.findByLabelText("Channel"), "@failing");
    await user.click(screen.getByRole("button", { name: "Save subscription" }));
    expect(await screen.findByText(/This channel does not exist/)).toBeVisible();
  });

  it("checks, pauses and deletes from the list", async () => {
    const server = createFakeServer();
    server.subscriptions = [
      makeSubscription({ id: 1, name: "Demo", last_error: "Couldn't load the channel feed" }),
    ];
    installFakeApi(server);
    const { user } = renderApp("/subscriptions");

    expect(await screen.findByText(/Not checked yet · every 10 min/)).toBeVisible();
    expect(screen.getByText("Couldn't load the channel feed")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Check Demo now" }));
    expect(await screen.findByText(/Checked just now/)).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Pause Demo" }));
    expect(await screen.findByText("Paused")).toBeVisible();
    expect(server.subscriptions[0]!.enabled).toBe(false);
    await user.click(screen.getByRole("button", { name: "Resume Demo" }));
    expect(await screen.findByRole("button", { name: "Pause Demo" })).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Delete Demo" }));
    await user.click(await screen.findByRole("button", { name: "Delete" }));
    expect(await screen.findByText("No channels watched yet")).toBeInTheDocument();
  });

  it("edits a subscription and lists its recent videos", async () => {
    const server = createFakeServer();
    server.subscriptions = [
      makeSubscription({
        id: 5,
        name: "Demo",
        output_dir: "demo",
        filters: { content_types: ["video"], min_duration: 120, include_members_only: false },
      }),
    ];
    server.videos = {
      5: [
        makeVideo({ id: 1, title: "Kept", state: "queued" }),
        makeVideo({ id: 2, title: "A Short", state: "skipped", reason: "It's a Short" }),
        makeVideo({ id: 3, title: "Soon", state: "upcoming", release_at: "2100-01-01T00:00:00Z" }),
      ],
    };
    installFakeApi(server);
    const { user } = renderApp("/subscriptions");

    await user.click(await screen.findByRole("link", { name: "Edit Demo" }));
    const videos = await screen.findByRole("list", { name: "Recent videos" });
    expect(within(videos).getByText("Downloading")).toBeVisible();
    expect(within(videos).getByText("It's a Short")).toBeVisible();
    expect(within(videos).getByText(/^Starts in \d+ years$/)).toBeVisible();
    expect(screen.queryByLabelText("Channel")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Shortest (minutes)")).toHaveValue("2");
    expect(screen.getByLabelText("Save to")).toHaveValue("demo");

    const poll = screen.getByLabelText("Check every (minutes)");
    await user.clear(poll);
    await user.type(poll, "30");
    await user.click(screen.getByRole("button", { name: "Save subscription" }));
    expect(await screen.findByText(/every 30 min/)).toBeVisible();
    expect(server.subscriptions[0]).toMatchObject({ poll_minutes: 30, output_dir: "demo" });
  });

  it("explains a subscription that no longer exists", async () => {
    installFakeApi(createFakeServer());
    renderApp("/subscriptions/9");
    expect(await screen.findByText("This subscription doesn't exist any more.")).toBeVisible();
  });
});
