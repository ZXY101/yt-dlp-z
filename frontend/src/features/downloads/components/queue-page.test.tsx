import { act, screen, within } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { makeJob } from "@/test/fake-jobs";
import { broadcast } from "@/test/fake-socket";
import { renderApp } from "@/test/render";

describe("QueuePage", () => {
  it("shows an empty state", async () => {
    installFakeApi(createFakeServer());
    renderApp("/queue");
    expect(await screen.findByText("No downloads yet")).toBeInTheDocument();
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
    });
    act(() => broadcast({ type: "job", job: running }));
    expect(await within(inProgress).findByText(/55% · 1.0 MB\/s/)).toBeInTheDocument();

    act(() => broadcast({ type: "job", job: { ...running, status: "completed", progress: 100 } }));
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
});
