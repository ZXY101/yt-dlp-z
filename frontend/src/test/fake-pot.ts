import { type FakeServer, type Route, json } from "@/test/fake-http";

const OFF = {
  url: null,
  server_version: null,
  error: null,
  checked_at: null,
  plugin_version: null,
};

export function makePot() {
  return { pot: { ...OFF }, potServerVersion: "2.0.2" as string | null };
}

const UNREACHABLE = { detail: "Couldn't reach the provider: Connection refused" };

function save(server: FakeServer, url: string | null) {
  if (url === null) {
    server.pot = { ...OFF };
    return json(server.pot);
  }
  const version = server.potServerVersion;
  if (version === null) {
    return json(UNREACHABLE, 502);
  }
  server.pot = {
    url,
    server_version: version,
    error: null,
    checked_at: "2026-11-03T12:00:00Z",
    plugin_version: version,
  };
  return json(server.pot);
}

export const potRoutes: Route[] = [
  { method: "GET", path: /^\/api\/ytdlp\/pot$/, handle: (server) => json(server.pot) },
  {
    method: "PUT",
    path: /^\/api\/ytdlp\/pot$/,
    handle: (server, { body }) => save(server, (body as { url: string | null }).url),
  },
  {
    method: "POST",
    path: /^\/api\/ytdlp\/pot\/test$/,
    handle: (server) => {
      const version = server.potServerVersion;
      return version === null ? json(UNREACHABLE, 502) : json({ server_version: version });
    },
  },
];
