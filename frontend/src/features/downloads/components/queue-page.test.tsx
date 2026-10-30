import { act, screen, within } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { makeJob } from "@/test/fake-jobs";
import { broadcast } from "@/test/fake-socket";
import { renderApp } from "@/test/render";

describe("QueuePage", () => {
  it("shows an empty state that links to the download page", async () => {
    installFakeApi(createFakeServer());
    const { user, router } = renderApp("/queue");
    await user.click(await screen.findByRole("link", { name: /No downloads yet/ }));
    expect(router.state.location.pathname).toBe("/");
  });

  it("groups jobs and updates progress live", async () => {
    const server = createFakeServer();
    server.jobs = [
      makeJob({ id: 1, status: "completed", title: "Old video", filepath: "/downloads/old.mp4" }),
      makeJob({ id: 2, status: "failed", title: "Broken video", error: "Video unavailable" }),
      makeJob({ id: 3, status: "running", title: "Current video", progress: 10 }),
    ];
    installFakeApi(server);
    renderApp("/queue");

    const inProgress = await screen.findByRole("list", { name: "In progress" });
    const finished = screen.getByRole("list", { name: "Finished" });
    expect(within(inProgress).getByText("Current video")).toBeInTheDocument();
    expect(within(finished).getByText("Saved to /downloads/old.mp4")).toBeInTheDocument();
    expect(within(finished).getByText("Video unavailable")).toBeInTheDocument();

    const running = makeJob({
      id: 3,
      status: "running",
      title: "Current video",
      progress: 55,
      speed: 1_000_000,
      revision: 1,
    });
    act(() => broadcast({ type: "job", job: running }));
    expect(await within(inProgress).findByText(/55% · 1.0 MB\/s/)).toBeInTheDocument();

    act(() =>
      broadcast({
        type: "job",
        job: { ...running, status: "completed", progress: 100, revision: 2 },
      }),
    );
    expect(await screen.findByRole("list", { name: "Finished" })).toHaveTextContent(
      "Current video",
    );
    expect(screen.queryByRole("list", { name: "In progress" })).not.toBeInTheDocument();
  });

  it("cancels, retries and removes downloads", async () => {
    const server = createFakeServer();
    server.jobs = [makeJob({ id: 1, status: "running", title: "Clip" })];
    installFakeApi(server);
    const { user } = renderApp("/queue");

    await user.click(await screen.findByRole("button", { name: "Cancel Clip" }));
    expect(await screen.findByText("Cancelled")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry Clip" }));
    expect(await screen.findByText("Queued")).toBeInTheDocument();
    expect(screen.getByText(/Waiting for a free download slot/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Cancel Clip" }));
    await user.click(await screen.findByRole("button", { name: "Remove Clip from the list" }));
    expect(await screen.findByText("No downloads yet")).toBeInTheDocument();
  });

  it("shows the download log", async () => {
    const server = createFakeServer();
    server.jobs = [makeJob({ id: 4, status: "failed", title: "Clip" })];
    server.logs[4] = "[youtube] Extracting URL\nERROR: Video unavailable";
    installFakeApi(server);
    const { user } = renderApp("/queue");

    await user.click(await screen.findByRole("button", { name: "Log" }));
    const dialog = await screen.findByRole("dialog");
    expect(await within(dialog).findByText(/ERROR: Video unavailable/)).toBeInTheDocument();
  });

  it("shows an error when an action fails", async () => {
    const server = createFakeServer();
    server.jobs = [makeJob({ id: 1, status: "running", title: "Clip" })];
    installFakeApi(server);
    const { user } = renderApp("/queue");

    const cancel = await screen.findByRole("button", { name: "Cancel Clip" });
    server.jobs = [];
    await user.click(cancel);
    expect(await screen.findByText("Download not found")).toBeInTheDocument();
  });

  it("shows recordings: scheduled ones in their own list, soonest first", async () => {
    const server = createFakeServer();
    const live = { kind: "live" as const };
    server.jobs = [
      makeJob({
        id: 1,
        ...live,
        status: "scheduled",
        title: "Later stream",
        scheduled_at: "2100-01-02T12:00:00+00:00",
      }),
      makeJob({
        id: 2,
        ...live,
        status: "scheduled",
        title: "Next stream",
        scheduled_at: "2100-01-01T12:00:00+00:00",
      }),
      makeJob({
        id: 3,
        ...live,
        status: "running",
        title: "Live now",
        downloaded_bytes: 5_000_000,
      }),
      makeJob({ id: 4, ...live, status: "queued", title: "Waiting stream" }),
    ];
    installFakeApi(server);
    const { user } = renderApp("/queue");

    const scheduled = await screen.findByRole("list", { name: "Scheduled" });
    const items = within(scheduled).getAllByRole("listitem");
    expect(items.map((item) => within(item).getAllByText(/stream$/)[0]?.textContent)).toEqual([
      "Next stream",
      "Later stream",
    ]);
    expect(within(items[0]!).getByText(/^Stream starts/)).toBeInTheDocument();

    const inProgress = screen.getByRole("list", { name: "In progress" });
    expect(within(inProgress).getByText("Recording")).toBeInTheDocument();
    expect(within(inProgress).getByText("5.0 MB")).toBeInTheDocument();
    expect(within(inProgress).queryByRole("progressbar")).not.toBeInTheDocument();
    expect(within(inProgress).getByText(/free recording slot/)).toBeInTheDocument();

    await user.click(within(scheduled).getByRole("button", { name: "Cancel Next stream" }));
    const finished = await screen.findByRole("list", { name: "Finished" });
    expect(within(finished).getByText("Next stream")).toBeInTheDocument();
  });

  it("shows which part a split recording is on, and what a stopped one saved", async () => {
    const server = createFakeServer();
    const live = { kind: "live" as const, part_seconds: 21_600 };
    server.jobs = [
      makeJob({
        id: 1,
        ...live,
        status: "running",
        title: "Long stream",
        part: 2,
        downloaded_bytes: 1_000_000,
      }),
      makeJob({
        id: 2,
        ...live,
        status: "cancelled",
        title: "Stopped stream",
        filepath: "/downloads/stopped (part 1).mp4",
      }),
    ];
    installFakeApi(server);
    renderApp("/queue");

    const inProgress = await screen.findByRole("list", { name: "In progress" });
    expect(within(inProgress).getByText(/^Part 2 · 1\.0 MB/)).toBeInTheDocument();
    const finished = screen.getByRole("list", { name: "Finished" });
    expect(
      within(finished).getByText("Saved to /downloads/stopped (part 1).mp4"),
    ).toBeInTheDocument();
  });
});
