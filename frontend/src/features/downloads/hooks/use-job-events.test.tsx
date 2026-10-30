import { act, screen, waitFor } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { makeJob } from "@/test/fake-jobs";
import { FakeWebSocket, broadcast } from "@/test/fake-socket";
import { renderApp } from "@/test/render";

function latestSocket() {
  const socket = FakeWebSocket.instances.at(-1);
  if (!socket) {
    throw new Error("No WebSocket was opened");
  }
  return socket;
}

describe("useJobEvents", () => {
  it("connects to the events endpoint on the current host", async () => {
    installFakeApi(createFakeServer());
    renderApp("/");
    await screen.findByRole("heading", { name: "Download" });
    expect(latestSocket().url).toBe(`ws://${window.location.host}/api/ws`);
  });

  it("reconnects after the connection drops and catches up", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    renderApp("/queue");
    await screen.findByText("No downloads yet");
    await waitFor(() => expect(latestSocket().readyState).toBe(1));

    server.jobs = [makeJob({ id: 9, title: "Missed while offline", status: "running" })];
    act(() => latestSocket().close(1006));

    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(2), { timeout: 2000 });
    expect(await screen.findByText("Missed while offline")).toBeInTheDocument();
    act(() =>
      broadcast({
        type: "job",
        job: makeJob({ id: 9, title: "Live again", status: "running", revision: 1 }),
      }),
    );
    expect(await screen.findByText("Live again")).toBeInTheDocument();
  });

  it("returns to the login page when the session has ended", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    renderApp("/");
    await screen.findByRole("heading", { name: "Download" });

    server.status = { ...server.status, authenticated: false };
    act(() => latestSocket().close(4401));
    expect(await screen.findByLabelText("Password")).toBeInTheDocument();
  });
});
