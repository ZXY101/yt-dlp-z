import { screen } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

const ADDRESS = "http://bgutil-provider:4416";

describe("PotSection", () => {
  it("is off until a provider is saved", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/settings");

    const field = await screen.findByLabelText("Provider address");
    expect(screen.getByText("Off.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Test" })).toBeDisabled();

    await user.type(field, ADDRESS);
    await user.click(screen.getByRole("button", { name: "Save provider" }));

    expect(await screen.findByText("PO tokens on.")).toBeInTheDocument();
    expect(screen.getByText("On: provider 2.0.2, plugin 2.0.2.")).toBeInTheDocument();
    expect(server.pot.url).toBe(ADDRESS);
  });

  it("tests a provider without saving it", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/settings");

    await user.type(await screen.findByLabelText("Provider address"), ADDRESS);
    await user.click(screen.getByRole("button", { name: "Test" }));

    expect(await screen.findByText("Provider 2.0.2 answered.")).toBeInTheDocument();
    expect(server.pot.url).toBeNull();
  });

  it("explains an unreachable provider", async () => {
    const server = createFakeServer();
    server.potServerVersion = null;
    installFakeApi(server);
    const { user } = renderApp("/settings");

    await user.type(await screen.findByLabelText("Provider address"), ADDRESS);
    await user.click(screen.getByRole("button", { name: "Save provider" }));

    expect(await screen.findByText(/Couldn't reach the provider/)).toBeInTheDocument();
    expect(server.pot.url).toBeNull();
  });

  it("turns off when the address is cleared, and shows a failed check", async () => {
    const server = createFakeServer();
    server.pot = {
      url: ADDRESS,
      server_version: null,
      error: "Couldn't reach the provider: timed out",
      checked_at: "2026-11-03T12:00:00Z",
      plugin_version: "2.0.2",
    };
    installFakeApi(server);
    const { user } = renderApp("/settings");

    expect(
      await screen.findByText(
        "On, but the last check failed: Couldn't reach the provider: timed out",
      ),
    ).toBeInTheDocument();

    await user.clear(screen.getByLabelText("Provider address"));
    await user.click(screen.getByRole("button", { name: "Save provider" }));

    expect(await screen.findByText("PO tokens off.")).toBeInTheDocument();
    expect(server.pot.url).toBeNull();
  });
});
