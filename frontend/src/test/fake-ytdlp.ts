import type { YtdlpInfo } from "@/features/settings/types";
import { type FakeServer, type Route, json } from "@/test/fake-http";

export function makeYtdlpInfo(): YtdlpInfo {
  return {
    bundled_version: "2026.10.26",
    active_version: "2026.10.26",
    using_update: false,
    channel: "stable",
    auto_update: false,
    update: { state: "idle", message: null, finished_at: null },
    latest_version: null,
    checked_at: null,
  };
}

const UPDATED_TO = { stable: "2099.1.1", nightly: "2099.1.2.dev0" };
const RUNNING = { detail: "An update is already running" };

/** An update started with POST finishes at the next GET, like a quick background job. */
function finishUpdate(server: FakeServer) {
  const info = server.ytdlp;
  if (info.update.state !== "running") {
    return;
  }
  if (server.ytdlpUpdateFails) {
    info.update = { state: "failed", message: "The update failed: no network", finished_at: null };
    return;
  }
  const version = UPDATED_TO[info.channel];
  Object.assign(info, { active_version: version, using_update: true });
  info.update = { state: "succeeded", message: `Updated yt-dlp to ${version}.`, finished_at: null };
}

export const ytdlpRoutes: Route[] = [
  {
    method: "GET",
    path: /^\/api\/ytdlp$/,
    handle: (server) => {
      finishUpdate(server);
      return json(server.ytdlp);
    },
  },
  {
    method: "PUT",
    path: /^\/api\/ytdlp\/preferences$/,
    handle: (server, { body }) => {
      server.ytdlp.channel = body.channel as YtdlpInfo["channel"];
      server.ytdlp.auto_update = Boolean(body.auto_update);
      return json(server.ytdlp);
    },
  },
  {
    method: "POST",
    path: /^\/api\/ytdlp\/check$/,
    handle: (server) => {
      server.ytdlp.latest_version = UPDATED_TO[server.ytdlp.channel];
      server.ytdlp.checked_at = "2026-10-31T09:00:00+00:00";
      return json(server.ytdlp);
    },
  },
  {
    method: "POST",
    path: /^\/api\/ytdlp\/update$/,
    handle: (server) => {
      if (server.ytdlp.update.state === "running") {
        return json(RUNNING, 409);
      }
      server.ytdlp.update = { state: "running", message: null, finished_at: null };
      return json(server.ytdlp, 202);
    },
  },
  {
    method: "DELETE",
    path: /^\/api\/ytdlp\/update$/,
    handle: (server) => {
      const { bundled_version: bundled } = server.ytdlp;
      Object.assign(server.ytdlp, { active_version: bundled, using_update: false });
      server.ytdlp.update = { state: "idle", message: null, finished_at: null };
      return json(server.ytdlp);
    },
  },
];
