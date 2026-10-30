import { screen } from "@testing-library/react";

import { systemWarnings } from "@/features/system/system-warnings";
import { createFakeServer, installFakeApi } from "@/test/fake-api";
import { renderApp } from "@/test/render";

const healthy = {
  ytdlp_version: "2026.10.26",
  ytdlp_error: null,
  ffmpeg_available: true,
  deno_available: true,
};

describe("systemWarnings", () => {
  it("is empty when everything is installed", () => {
    expect(systemWarnings(healthy)).toEqual([]);
  });

  it("explains each missing piece", () => {
    const warnings = systemWarnings({
      ytdlp_version: null,
      ytdlp_error: "No module named yt_dlp",
      ffmpeg_available: false,
      deno_available: false,
    });
    expect(warnings).toHaveLength(3);
    expect(warnings[0]).toContain("No module named yt_dlp");
  });
});

describe("SystemWarnings", () => {
  it("shows warnings on the download page", async () => {
    const server = createFakeServer();
    server.system = { ...healthy, ffmpeg_available: false };
    installFakeApi(server);
    renderApp("/");

    expect(await screen.findByText("Setup needs attention")).toBeInTheDocument();
    expect(screen.getByText(/ffmpeg wasn't found/)).toBeInTheDocument();
  });
});
