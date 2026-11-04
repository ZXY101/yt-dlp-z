import { screen, within } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { makeJob } from "@/test/fake-jobs";
import { renderApp } from "@/test/render";

function savedJob(chatStatus: "saved" | "overlay" | "none" | "failed" | "stopped") {
  return makeJob({
    id: 1,
    status: "completed",
    title: "A stream",
    filepath: "/downloads/a.mp4",
    chat_status: chatStatus,
  });
}

function setUp(...jobs: ReturnType<typeof makeJob>[]) {
  const server = createFakeServer();
  server.jobs = jobs;
  installFakeApi(server);
  return { server, ...renderApp("/queue") };
}

describe("live chat in the queue", () => {
  it("says the chat is being fetched while the video is already saved", async () => {
    setUp(makeJob({ status: "running", title: "A stream", chat_status: "fetching" }));
    expect(await screen.findByText("Video saved. Fetching its live chat…")).toBeVisible();
    expect(screen.queryByRole("progressbar")).toBeNull();
  });

  it("says a recording is saving its chat", async () => {
    setUp(makeJob({ status: "running", kind: "live", title: "Live", chat_status: "capturing" }));
    expect(await screen.findByText(/saving live chat/)).toBeVisible();
  });

  it.each([
    ["saved", "Live chat saved."],
    ["overlay", "Live chat saved, with an overlay."],
    ["none", "This stream has no chat replay."],
    ["failed", "The video is saved, but its live chat isn't complete. See the log."],
    ["stopped", "The video is saved. Fetching its live chat was stopped."],
  ] as const)("reports a chat that ended as %s", async (status, note) => {
    setUp(savedJob(status));
    expect(await screen.findByText(note)).toBeVisible();
  });

  it("offers a rebuild only when there may be a saved chat", async () => {
    setUp(savedJob("none"), { ...savedJob("saved"), id: 2, title: "Saved one" });
    await screen.findByText("Saved one");
    expect(screen.getByRole("button", { name: "Chat overlay of Saved one" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Chat overlay of A stream" })).toBeNull();
  });

  it("rebuilds the overlay with the chosen look", async () => {
    const { server, user } = setUp(savedJob("saved"));
    await user.click(await screen.findByRole("button", { name: "Chat overlay of A stream" }));
    const dialog = await screen.findByRole("dialog");

    const limit = within(dialog).getByLabelText("Most comments on screen");
    expect(limit).toHaveValue("30");
    await user.clear(limit);
    await user.type(limit, "12");
    await user.selectOptions(within(dialog).getByLabelText("Comment colours"), "staff");
    await user.clear(within(dialog).getByLabelText("Opacity (%)"));
    await user.type(within(dialog).getByLabelText("Opacity (%)"), "50");
    await user.click(within(dialog).getByRole("button", { name: "Rebuild overlay" }));

    expect(await screen.findByText("Live chat saved, with an overlay.")).toBeVisible();
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(server.jobs[0]?.live_chat).toMatchObject({
      max_on_screen: 12,
      colour_mode: "staff",
      opacity: 0.5,
    });
  });

  it("shows why a rebuild failed", async () => {
    const { user } = setUp(savedJob("failed"));
    await user.click(await screen.findByRole("button", { name: "Chat overlay of A stream" }));
    await user.click(await screen.findByRole("button", { name: "Rebuild overlay" }));
    expect(await screen.findByText("This download has no saved live chat")).toBeVisible();
  });

  it("goes back to the last good number when the text isn't valid", async () => {
    const { server, user } = setUp(savedJob("saved"));
    await user.click(await screen.findByRole("button", { name: "Chat overlay of A stream" }));
    const size = await screen.findByLabelText("Text size");
    await user.clear(size);
    await user.type(size, "5");
    expect(screen.getByText("Enter a whole number from 16 to 120.")).toBeVisible();
    await user.tab();
    expect(size).toHaveValue("48");
    expect(screen.queryByText("Enter a whole number from 16 to 120.")).toBeNull();
    await user.click(screen.getByRole("button", { name: "Rebuild overlay" }));
    await screen.findByText("Live chat saved, with an overlay.");
    expect(server.jobs[0]?.live_chat).toMatchObject({ font_size: 48 });
  });
});
