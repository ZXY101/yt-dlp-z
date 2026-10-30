import { screen, waitFor } from "@testing-library/react";

import { parentOf } from "@/hooks/use-folder-suggestions";
import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

function suggestions() {
  const list = document.getElementById(screen.getByLabelText("Save to").getAttribute("list")!);
  return [...list!.querySelectorAll("option")].map((option) => option.value);
}

describe("FolderField", () => {
  it("suggests existing folders once the field is used", async () => {
    const server = createFakeServer();
    server.folders = { "": ["Music", "videos"], "Music/": ["Music/Albums"] };
    installFakeApi(server);
    const { user } = renderApp("/");

    const field = await screen.findByLabelText("Save to");
    expect(server.requests).not.toContain("GET /api/folders");
    await user.click(field);
    await waitFor(() => expect(suggestions()).toEqual(["Music", "videos"]));

    await user.type(field, "Music/Al");
    await waitFor(() => expect(suggestions()).toEqual(["Music/Albums"]));
  });

  it.each([
    ["", ""],
    ["music", ""],
    ["music/", "music/"],
    ["music/al", "music/"],
    ["/srv/media/x", "/srv/media/"],
  ])("takes the folder part of %j", (value, parent) => {
    expect(parentOf(value)).toBe(parent);
  });
});
