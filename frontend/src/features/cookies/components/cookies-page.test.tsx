import { screen, within } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { makeCookieFile } from "@/test/fake-library";
import { renderApp } from "@/test/render";

const COOKIES_TXT = [
  "# Netscape HTTP Cookie File",
  ".youtube.com\tTRUE\t/\tTRUE\t0\tPREF\tfake",
  ".google.com\tTRUE\t/\tTRUE\t0\tSID\tfake",
].join("\n");

function cookiesFile(content = COOKIES_TXT) {
  return new File([content], "cookies.txt", { type: "text/plain" });
}

describe("Cookies", () => {
  it("uploads a cookies file and lists its summary", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/cookies");

    // The empty state jumps to the upload form above it.
    await user.click(await screen.findByRole("button", { name: /No cookies yet/ }));
    expect(screen.getByLabelText("Name")).toHaveFocus();
    await user.type(screen.getByLabelText("Name"), "YouTube");
    await user.upload(screen.getByLabelText("Cookies file"), cookiesFile());
    await user.click(screen.getByRole("button", { name: "Upload" }));

    const list = await screen.findByRole("list", { name: "Cookies files" });
    expect(within(list).getByText("YouTube")).toBeInTheDocument();
    expect(within(list).getByText("2 cookies for youtube.com, google.com")).toBeInTheDocument();
    expect(screen.getByLabelText("Name")).toHaveValue("");
  });

  it("checks the form and shows invalid files", async () => {
    installFakeApi(createFakeServer());
    const { user } = renderApp("/cookies");

    await user.click(await screen.findByRole("button", { name: "Upload" }));
    expect(screen.getByText("Give the file a name, e.g. YouTube.")).toBeInTheDocument();
    expect(screen.getByText("Choose a cookies.txt file.")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Name"), "Broken");
    await user.upload(screen.getByLabelText("Cookies file"), cookiesFile("SID=abc"));
    await user.click(screen.getByRole("button", { name: "Upload" }));
    expect(await screen.findByText(/Netscape cookies.txt format/)).toBeInTheDocument();
  });

  it("tests cookies against a page", async () => {
    const server = createFakeServer();
    server.cookieFiles = [makeCookieFile({ name: "YouTube" })];
    installFakeApi(server);
    const { user } = renderApp("/cookies");

    await user.click(await screen.findByRole("button", { name: "Test" }));
    const dialog = screen.getByRole("dialog");
    const testButton = within(dialog).getByRole("button", { name: "Test" });
    expect(testButton).toBeDisabled();
    await user.type(within(dialog).getByLabelText("Page to open"), "https://example.com/members");
    await user.click(testButton);
    expect(await within(dialog).findByText(/Opened “Members video”/)).toBeInTheDocument();

    await user.clear(within(dialog).getByLabelText("Page to open"));
    await user.type(within(dialog).getByLabelText("Page to open"), "https://example.com/fail");
    await user.click(testButton);
    expect(await within(dialog).findByText(/Sign in to confirm/)).toBeInTheDocument();
  });

  it("replaces and deletes a cookies file", async () => {
    const server = createFakeServer();
    server.cookieFiles = [
      makeCookieFile({
        name: "YouTube",
        cookie_count: 1,
        domains: ["a.com", "b.com", "c.com", "d.com"],
      }),
    ];
    installFakeApi(server);
    const { user } = renderApp("/cookies");

    expect(await screen.findByText("1 cookie for a.com, b.com, c.com and 1 more")).toBeVisible();
    await user.upload(screen.getByLabelText("New cookies file for YouTube"), cookiesFile());
    expect(await screen.findByText("2 cookies for youtube.com, google.com")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Delete YouTube" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Delete" }));
    expect(await screen.findByText("No cookies yet")).toBeInTheDocument();
  });

  it("shows load errors", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    server.failWith = 500;
    renderApp("/cookies");
    expect(await screen.findByText("Server error")).toBeInTheDocument();
  });
});
