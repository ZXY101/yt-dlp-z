import { screen, waitFor, within } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

describe("AppLayout", () => {
  it("opens the mobile menu and closes it after navigating", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/");

    await user.click(await screen.findByRole("button", { name: "Open menu" }));
    const menu = await screen.findByRole("dialog");
    await user.click(within(menu).getByRole("link", { name: "Dashboard" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });

  it("hides sign out when auth is handled by a proxy", async () => {
    installFakeApi(createFakeServer({ auth_mode: "none" }));
    renderApp("/");

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Sign out" })).not.toBeInTheDocument();
  });
});
