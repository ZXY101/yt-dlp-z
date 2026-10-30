import { screen, within } from "@testing-library/react";

import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

async function openEditor() {
  const server = createFakeServer();
  installFakeApi(server);
  const result = renderApp("/");
  await result.user.click(await screen.findByRole("button", { name: "Advanced options" }));
  await result.user.click(screen.getByRole("button", { name: "All yt-dlp options" }));
  await screen.findByLabelText("Search options");
  return { server, ...result };
}

describe("OptionsEditor", () => {
  it("edits options of every kind and sends them with the download", async () => {
    const { server, user } = await openEditor();

    await user.click(screen.getByRole("button", { name: /Network Options/ }));
    await user.type(screen.getByLabelText("--proxy URL"), "socks5://proxy:1080");
    await user.click(screen.getByLabelText("--force-ipv4"));
    expect(screen.getByRole("button", { name: /Network Options/ })).toHaveTextContent("2 set");

    await user.click(screen.getByRole("button", { name: /Download Options/ }));
    await user.type(screen.getByLabelText("--retries RETRIES"), "5");
    await user.click(screen.getByRole("button", { name: /Post-Processing Options/ }));
    await user.selectOptions(screen.getByLabelText("--remux-video"), "mkv");
    const categories = screen.getByLabelText("--sponsorblock-remove");
    await user.type(categories, "sponsor{Enter}{Enter}intro");

    await user.type(screen.getByLabelText("Link"), "https://example.com/v");
    await user.click(screen.getByRole("button", { name: "Download" }));
    await screen.findByRole("heading", { name: "Queue" });
    expect(server.jobs[0]!.options).toEqual({
      "--embed-metadata": true,
      "--embed-thumbnail": true,
      "--proxy": "socks5://proxy:1080",
      "--force-ipv4": true,
      "--retries": "5",
      "--remux-video": "mkv",
      "--sponsorblock-remove": ["sponsor", "intro"],
    });
  });

  it("keeps the curated choices and the full list in sync", async () => {
    const { user } = await openEditor();
    await user.click(screen.getByLabelText("Embed subtitles"));
    await user.click(screen.getByRole("button", { name: /Post-Processing Options/ }));
    expect(screen.getByLabelText("--embed-subs")).toBeChecked();

    await user.click(screen.getByLabelText("--embed-metadata"));
    expect(screen.getByLabelText("Embed thumbnail and metadata")).not.toBeChecked();
  });

  it("searches flags and help text and can show only set options", async () => {
    const { user } = await openEditor();
    await user.type(screen.getByLabelText("Search options"), "proxy");
    expect(screen.getByLabelText("--proxy URL")).toBeVisible();
    expect(screen.queryByLabelText("--retries RETRIES")).not.toBeInTheDocument();

    await user.clear(screen.getByLabelText("Search options"));
    await user.type(screen.getByLabelText("Search options"), "no such option");
    expect(screen.getByText("No options match.")).toBeInTheDocument();

    await user.clear(screen.getByLabelText("Search options"));
    await user.click(screen.getByLabelText("Only options that are set"));
    expect(screen.getByLabelText("--embed-thumbnail")).toBeChecked();
    expect(screen.queryByLabelText("--embed-subs")).not.toBeInTheDocument();
  });

  it("shows blocked options as disabled with the reason", async () => {
    const { user } = await openEditor();
    await user.click(screen.getByRole("button", { name: /Download Options/ }));
    const blocked = screen.getByLabelText("--exec");
    expect(blocked).toBeDisabled();
    expect(
      within(blocked.parentElement!).getByText(/Blocked: It runs shell commands/),
    ).toBeVisible();
  });

  it("explains when the options can't be loaded", async () => {
    const server = createFakeServer();
    installFakeApi(server);
    const { user } = renderApp("/");
    await user.click(await screen.findByRole("button", { name: "Advanced options" }));
    server.failWith = 503;
    await user.click(screen.getByRole("button", { name: "All yt-dlp options" }));
    expect(await screen.findByText("Server error")).toBeInTheDocument();
  });
});
