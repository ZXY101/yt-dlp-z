import { screen, waitFor, within } from "@testing-library/react";

import { parentOf } from "@/hooks/use-folder-suggestions";
import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

function folderList() {
  return within(screen.getByRole("listbox", { name: "Existing folders" }));
}

function suggestions() {
  return folderList()
    .queryAllByRole("option")
    .map((option) => option.textContent);
}

describe("FolderField", () => {
  it("suggests existing folders once the field is used", async () => {
    const server = createFakeServer();
    server.folders = { "": ["Music", "videos"], "Music/": ["Music/Albums", "Music/Live"] };
    installFakeApi(server);
    const { user } = renderApp("/");

    const field = await screen.findByRole("combobox", { name: "Save to" });
    expect(server.requests).not.toContain("GET /api/folders");
    await user.click(field);
    await waitFor(() => expect(suggestions()).toEqual(["Music", "videos"]));

    await user.click(folderList().getByRole("option", { name: "Music" }));
    expect(field).toHaveValue("Music/");
    await waitFor(() => expect(suggestions()).toEqual(["Music/Albums", "Music/Live"]));
    await user.type(field, "l");
    expect(suggestions()).toEqual(["Music/Live"]);
  });

  it("works with the keyboard", async () => {
    const server = createFakeServer();
    server.folders = { "": ["Music", "videos"] };
    installFakeApi(server);
    const { user } = renderApp("/");

    const field = await screen.findByRole("combobox", { name: "Save to" });
    await user.click(field);
    await waitFor(() => expect(field).toHaveAttribute("aria-expanded", "true"));
    await user.keyboard("{ArrowDown}{ArrowDown}");
    expect(folderList().getByRole("option", { name: "videos" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await user.keyboard("{ArrowUp}{ArrowUp}");
    expect(folderList().getByRole("option", { name: "videos" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await user.keyboard("{Enter}");
    expect(field).toHaveValue("videos/");

    await user.clear(field);
    expect(field).toHaveAttribute("aria-expanded", "true");
    await user.keyboard("{Escape}");
    expect(field).toHaveAttribute("aria-expanded", "false");
    await user.keyboard("{ArrowDown}");
    expect(field).toHaveAttribute("aria-expanded", "true");
    await user.tab();
    expect(field).toHaveAttribute("aria-expanded", "false");
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
