import { screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { FAKE_TOKEN } from "@/test/fake-tokens";
import { renderApp } from "@/test/render";

describe("API tokens", () => {
  it("shows a new token once, with the command to add it", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/settings");

    await user.type(await screen.findByLabelText("Token name"), "Claude Code");
    await user.click(screen.getByRole("button", { name: "Create token" }));

    expect(await screen.findByText(FAKE_TOKEN)).toBeInTheDocument();
    expect(screen.getByText(/claude mcp add --transport http yt-dlp-z/)).toBeInTheDocument();
    expect(await screen.findByText("Never used")).toBeInTheDocument();
    expect(screen.getByLabelText("Token name")).toHaveValue("");
  });

  it("revokes a token after asking", async () => {
    const server = createFakeServer();
    server.apiTokens = [
      {
        id: 1,
        name: "Old agent",
        created_at: "2026-11-01T10:00:00Z",
        last_used_at: "2026-11-02T10:00:00Z",
      },
    ];
    installFakeApi(server);
    const { user } = renderApp("/settings");

    await user.click(await screen.findByRole("button", { name: "Revoke Old agent" }));
    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: "Revoke" }));

    await waitFor(() => expect(server.apiTokens).toEqual([]));
    await waitFor(() => expect(screen.queryByText("Old agent")).not.toBeInTheDocument());
  });
});
