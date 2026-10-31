import type { components } from "@/api/generated/schema";
import { type FakeServer, type Route, json, noContent } from "@/test/fake-http";

type Proxy = components["schemas"]["ProxyOut"];

const ADDRESS = /^(https?|socks4a?|socks5h?):\/\/[^/]+:\d+$/;

export function makeProxy(overrides: Partial<Proxy> = {}): Proxy {
  return {
    id: 1,
    name: "VPN 1",
    url: "socks5://vpn-1:1080",
    enabled: true,
    cooldown_until: null,
    checked_at: null,
    check_ok: null,
    exit_ip: null,
    check_error: null,
    ...overrides,
  };
}

/** Like the real API, passwords never come back. */
function masked(url: string) {
  return url.replace(/:\/\/([^:@/]*):[^@/]*@/, "://$1:****@");
}

function findProxy(server: FakeServer, params: string[]) {
  return server.proxies.find((proxy) => proxy.id === Number(params[0]));
}

function rejection(server: FakeServer, existing: Proxy | null, body: Record<string, unknown>) {
  const name = String(body.name ?? "");
  if (server.proxies.some((proxy) => proxy.name === name && proxy.id !== existing?.id)) {
    return json({ detail: `A proxy named '${name}' already exists` }, 409);
  }
  if (typeof body.url === "string" && !ADDRESS.test(body.url)) {
    return json({ detail: "Enter scheme://host:port" }, 422);
  }
  return null;
}

function saveProxy(server: FakeServer, existing: Proxy | null, body: Record<string, unknown>) {
  const rejected = rejection(server, existing, body);
  if (rejected) {
    return rejected;
  }
  const name = String(body.name);
  const url = typeof body.url === "string" ? body.url : null;
  const id = existing?.id ?? Math.max(0, ...server.proxies.map((proxy) => proxy.id)) + 1;
  const saved = makeProxy({
    ...existing,
    id,
    name,
    enabled: body.enabled !== false,
    url: url === null ? (existing?.url ?? "") : masked(url),
  });
  server.proxies = [...server.proxies.filter((proxy) => proxy.id !== id), saved];
  server.proxies.sort((a, b) => a.id - b.id);
  return json(saved, existing ? 200 : 201);
}

function checkProxy(proxy: Proxy) {
  const works = !proxy.url.includes("dead");
  Object.assign(proxy, {
    checked_at: "2026-10-31T10:00:00+00:00",
    check_ok: works,
    exit_ip: works ? "203.0.113.7 (ZZ)" : null,
    check_error: works ? null : "Unable to connect to proxy",
  });
  return json(proxy);
}

export const proxyRoutes: Route[] = [
  {
    method: "GET",
    path: /^\/api\/proxies\/settings$/,
    handle: (server) => json(server.proxySettings),
  },
  {
    method: "PUT",
    path: /^\/api\/proxies\/settings$/,
    handle: (server, { body }) => {
      server.proxySettings = { send_cookies: body.send_cookies === true };
      return json(server.proxySettings);
    },
  },
  { method: "GET", path: /^\/api\/proxies$/, handle: (server) => json(server.proxies) },
  {
    method: "POST",
    path: /^\/api\/proxies$/,
    handle: (server, { body }) => saveProxy(server, null, body),
  },
  {
    method: "PUT",
    path: /^\/api\/proxies\/(\d+)$/,
    handle: (server, { body, params }) => {
      const proxy = findProxy(server, params);
      return proxy ? saveProxy(server, proxy, body) : json({ detail: "Proxy not found" }, 404);
    },
  },
  {
    method: "DELETE",
    path: /^\/api\/proxies\/(\d+)$/,
    handle: (server, { params }) => {
      server.proxies = server.proxies.filter((proxy) => proxy.id !== Number(params[0]));
      return noContent();
    },
  },
  {
    method: "POST",
    path: /^\/api\/proxies\/(\d+)\/check$/,
    handle: (server, { params }) => {
      const proxy = findProxy(server, params);
      return proxy ? checkProxy(proxy) : json({ detail: "Proxy not found" }, 404);
    },
  },
];
