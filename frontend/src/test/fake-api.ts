import type { AuthStatus } from "@/features/auth/types";
import { type FakeServer, type Route, json, noContent } from "@/test/fake-http";
import { jobRoutes } from "@/test/fake-jobs";
import { libraryRoutes } from "@/test/fake-library";
import { mediaRoutes } from "@/test/fake-media";
import { subscriptionRoutes } from "@/test/fake-subscriptions";
import { installFakeSocket } from "@/test/fake-socket";
import { makeYtdlpInfo, ytdlpRoutes } from "@/test/fake-ytdlp";

export type { FakeServer } from "@/test/fake-http";

export const FAKE_PASSWORD = "fake-password-123";

const authRoutes: Route[] = [
  { method: "GET", path: /^\/api\/auth\/status$/, handle: (server) => json(server.status) },
  {
    method: "POST",
    path: /^\/api\/auth\/setup$/,
    handle: (server, { body }) => {
      if (server.status.password_from_env && body.password !== FAKE_PASSWORD) {
        return json({ detail: "Incorrect password" }, 401);
      }
      server.status = { ...server.status, setup_required: false, authenticated: true };
      return noContent();
    },
  },
  {
    method: "POST",
    path: /^\/api\/auth\/login$/,
    handle: (server, { body }) => {
      if (body.password !== FAKE_PASSWORD) {
        return json({ detail: "Incorrect password" }, 401);
      }
      server.status = { ...server.status, authenticated: true };
      return noContent();
    },
  },
  {
    method: "POST",
    path: /^\/api\/auth\/logout$/,
    handle: (server) => {
      server.status = { ...server.status, authenticated: false };
      return noContent();
    },
  },
];

const routes = [
  ...authRoutes,
  ...jobRoutes,
  ...mediaRoutes,
  ...libraryRoutes,
  ...subscriptionRoutes,
  ...ytdlpRoutes,
];

export function createFakeServer(status: Partial<AuthStatus> = {}): FakeServer {
  return {
    status: {
      setup_required: false,
      authenticated: true,
      auth_mode: "password",
      password_from_env: false,
      default_download_dir: "/downloads",
      ...status,
    },
    failWith: null,
    requests: [],
    jobs: [],
    nextJobId: 1,
    logs: {},
    system: {
      ytdlp_version: "2026.10.26",
      ytdlp_error: null,
      ffmpeg_available: true,
      deno_available: true,
    },
    presets: [],
    cookieFiles: [],
    settings: {
      download_dir: "/downloads",
      max_concurrent_downloads: 3,
      max_concurrent_recordings: 2,
      max_subscriptions: 5,
      recording: {
        part_hours: 6,
        max_hours: null,
        from_start_max_hours: 6,
        long_streams: "from_now",
      },
    },
    folders: {},
    ytdlp: makeYtdlpInfo(),
    ytdlpUpdateFails: false,
    subscriptions: [],
    videos: {},
  };
}

function findRoute(method: string, pathname: string) {
  for (const route of routes) {
    const match = route.method === method ? route.path.exec(pathname) : null;
    if (match) {
      return { route, params: match.slice(1) };
    }
  }
  return undefined;
}

async function handle(server: FakeServer, request: Request) {
  const { pathname, searchParams } = new URL(request.url);
  server.requests.push(`${request.method} ${pathname}`);
  if (server.failWith) {
    return json({ detail: "Server error" }, server.failWith);
  }
  const found = findRoute(request.method, pathname);
  if (!found) {
    return json({ detail: "Not Found" }, 404);
  }
  const text = await request.text();
  return found.route.handle(server, {
    body: text ? JSON.parse(text) : {},
    params: found.params,
    query: searchParams,
  });
}

export function installFakeApi(server: FakeServer) {
  vi.stubGlobal("fetch", (request: Request) => handle(server, request));
  installFakeSocket();
}
