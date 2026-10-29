import type { AuthStatus } from "@/features/auth/types";

export const FAKE_PASSWORD = "fake-password-123";

export interface FakeServer {
  status: AuthStatus;
  /** When set, every request fails with this HTTP status. */
  failWith: number | null;
  requests: string[];
}

type Handler = (server: FakeServer, body: Record<string, unknown>) => Response;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function noContent() {
  return new Response(null, { status: 204 });
}

const handlers: Record<string, Handler> = {
  "GET /api/auth/status": (server) => json(server.status),
  "POST /api/auth/setup": (server) => {
    server.status = { ...server.status, setup_required: false, authenticated: true };
    return noContent();
  },
  "POST /api/auth/login": (server, body) => {
    if (body.password !== FAKE_PASSWORD) {
      return json({ detail: "Incorrect password" }, 401);
    }
    server.status = { ...server.status, authenticated: true };
    return noContent();
  },
  "POST /api/auth/logout": (server) => {
    server.status = { ...server.status, authenticated: false };
    return noContent();
  },
};

export function createFakeServer(status: Partial<AuthStatus> = {}): FakeServer {
  return {
    status: {
      setup_required: false,
      authenticated: true,
      auth_mode: "password",
      default_download_dir: "/downloads",
      ...status,
    },
    failWith: null,
    requests: [],
  };
}

async function handle(server: FakeServer, request: Request) {
  const route = `${request.method} ${new URL(request.url).pathname}`;
  server.requests.push(route);
  if (server.failWith) {
    return json({ detail: "Server error" }, server.failWith);
  }
  const handler = handlers[route];
  if (!handler) {
    return json({ detail: "Not Found" }, 404);
  }
  const text = await request.text();
  return handler(server, text ? JSON.parse(text) : {});
}

export function installFakeApi(server: FakeServer) {
  vi.stubGlobal("fetch", (request: Request) => handle(server, request));
}
