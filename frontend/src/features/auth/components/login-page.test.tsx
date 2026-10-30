import { screen } from "@testing-library/react";

import { FAKE_PASSWORD, createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

describe("LoginPage", () => {
  it("rejects a wrong password, then signs in and out", async () => {
    installFakeApi(createFakeServer({ authenticated: false }));
    const { user, router } = renderApp("/");

    const password = await screen.findByLabelText("Password");
    expect(router.state.location.pathname).toBe("/login");

    await user.type(password, "wrong");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("Incorrect password")).toBeInTheDocument();

    await user.clear(password);
    await user.type(password, FAKE_PASSWORD);
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("heading", { name: "Download" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Sign out" }));
    expect(await screen.findByLabelText("Password")).toBeInTheDocument();
  });

  it("sends signed-in users away from the login page", async () => {
    installFakeApi(createFakeServer());
    const { router } = renderApp("/login");

    expect(await screen.findByRole("heading", { name: "Download" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/");
  });
});
