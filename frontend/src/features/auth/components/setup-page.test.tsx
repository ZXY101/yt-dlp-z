import { screen } from "@testing-library/react";

import { FAKE_PASSWORD, createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

describe("SetupPage", () => {
  it("sends a fresh install to setup and finishes on the download page", async () => {
    const server = createFakeServer({ setup_required: true, authenticated: false });
    installFakeApi(server);
    const { user, router } = renderApp("/");

    expect(await screen.findByRole("heading", { name: /welcome/i })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/setup");
    expect(screen.getByLabelText("Download folder")).toHaveValue("/downloads");

    await user.type(screen.getByLabelText("Admin password"), "long-enough");
    await user.type(screen.getByLabelText("Repeat password"), "long-enough");
    await user.click(screen.getByRole("button", { name: "Finish setup" }));

    expect(await screen.findByRole("heading", { name: "Download" })).toBeInTheDocument();
    expect(server.requests).toContain("POST /api/auth/setup");
  });

  it("shows validation errors without calling the API", async () => {
    const server = createFakeServer({ setup_required: true, authenticated: false });
    installFakeApi(server);
    const { user } = renderApp("/setup");

    await user.type(await screen.findByLabelText("Admin password"), "short");
    await user.clear(screen.getByLabelText("Download folder"));
    await user.click(screen.getByRole("button", { name: "Finish setup" }));

    expect(screen.getByText("Use at least 8 characters.")).toBeInTheDocument();
    expect(screen.getByText("Choose a download folder.")).toBeInTheDocument();
    expect(server.requests).not.toContain("POST /api/auth/setup");
  });

  it("hides password fields when auth is handled by a proxy", async () => {
    installFakeApi(createFakeServer({ setup_required: true, auth_mode: "none" }));
    renderApp("/setup");

    expect(await screen.findByLabelText("Download folder")).toBeInTheDocument();
    expect(screen.queryByLabelText("Admin password")).not.toBeInTheDocument();
  });

  it("shows server errors", async () => {
    const server = createFakeServer({ setup_required: true, authenticated: false });
    installFakeApi(server);
    const { user } = renderApp("/setup");

    await user.type(await screen.findByLabelText("Admin password"), "long-enough");
    await user.type(screen.getByLabelText("Repeat password"), "long-enough");
    server.failWith = 500;
    await user.click(screen.getByRole("button", { name: "Finish setup" }));

    expect(await screen.findByText("Server error")).toBeInTheDocument();
  });

  it("asks for the env-configured password instead of creating one", async () => {
    const server = createFakeServer({ setup_required: true, password_from_env: true });
    installFakeApi(server);
    const { user } = renderApp("/setup");

    const password = await screen.findByLabelText("Admin password");
    expect(screen.queryByLabelText("Repeat password")).not.toBeInTheDocument();
    expect(screen.getByText(/YTDLPZ_ADMIN_PASSWORD/)).toBeInTheDocument();

    await user.type(password, "wrong");
    await user.click(screen.getByRole("button", { name: "Finish setup" }));
    expect(await screen.findByText("Incorrect password")).toBeInTheDocument();

    await user.clear(password);
    await user.type(password, FAKE_PASSWORD);
    await user.click(screen.getByRole("button", { name: "Finish setup" }));
    expect(await screen.findByRole("heading", { name: "Download" })).toBeInTheDocument();
  });
});
