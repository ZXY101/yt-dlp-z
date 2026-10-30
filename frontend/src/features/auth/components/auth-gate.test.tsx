import { screen } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

describe("AuthGate", () => {
  it("shows a retryable error when the server is unreachable", async () => {
    const server = createFakeServer();
    server.failWith = 502;
    installFakeApi(server);
    const { user } = renderApp("/");

    expect(await screen.findByText("Can't reach the server")).toBeInTheDocument();

    server.failWith = null;
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: "Download" })).toBeInTheDocument();
  });
});
