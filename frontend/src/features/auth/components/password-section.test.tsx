import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { createFakeServer, FAKE_PASSWORD, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

async function fillPasswords(user: ReturnType<typeof renderApp>["user"], current: string) {
  await user.type(await screen.findByLabelText("Current password"), current);
  await user.type(screen.getByLabelText("New password"), "brand-new-password");
  await user.type(screen.getByLabelText("Repeat new password"), "brand-new-password");
  await user.click(screen.getByRole("button", { name: "Change password" }));
}

describe("password", () => {
  it("can be changed in Settings", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/settings");
    await fillPasswords(user, FAKE_PASSWORD);
    expect(await screen.findByText(/Password changed/)).toBeInTheDocument();
    expect(screen.getByLabelText("Current password")).toHaveValue("");
  });

  it("says when the current password is wrong", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/settings");
    await fillPasswords(user, "wrong-password");
    expect(await screen.findByText("Incorrect password")).toBeInTheDocument();
  });

  it("checks the new password before sending it", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/settings");
    await user.type(await screen.findByLabelText("Current password"), FAKE_PASSWORD);
    await user.type(screen.getByLabelText("New password"), "short");
    await user.click(screen.getByRole("button", { name: "Change password" }));
    expect(await screen.findByText(/Use at least 8 characters/)).toBeInTheDocument();
  });

  it("points to the environment variable when the password comes from it", async () => {
    const server = createFakeServer();
    server.status = { ...server.status, password_from_env: true };
    installFakeApi(server);
    renderApp("/settings");
    expect(await screen.findByText(/Change it there and restart/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Current password")).not.toBeInTheDocument();
  });

  it("is hidden when the server runs without a password", async () => {
    const server = createFakeServer();
    server.status = { ...server.status, auth_mode: "none" };
    installFakeApi(server);
    renderApp("/settings");
    expect(await screen.findByRole("heading", { name: "API tokens" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Password" })).not.toBeInTheDocument();
  });
});
