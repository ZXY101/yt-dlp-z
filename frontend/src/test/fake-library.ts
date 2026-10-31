import type { components } from "@/api/generated/schema";
import { type FakeServer, type Route, json, noContent } from "@/test/fake-http";
import { FAKE_SCHEMA } from "@/test/fake-schema";

type Preset = components["schemas"]["PresetOut"];
type CookieFile = components["schemas"]["CookieFileOut"];

const NOW = "2026-10-30T10:00:00+00:00";

export function makePreset(overrides: Partial<Preset> = {}): Preset {
  return {
    id: 1,
    name: "Music",
    options: {},
    extra_args: "",
    output_dir: null,
    cookie_id: null,
    kind: "any",
    is_default: false,
    recording: null,
    created_at: NOW,
    updated_at: NOW,
    ...overrides,
  };
}

export function makeCookieFile(overrides: Partial<CookieFile> = {}): CookieFile {
  return {
    id: 1,
    name: "YouTube",
    cookie_count: 12,
    domains: ["youtube.com"],
    created_at: NOW,
    updated_at: NOW,
    ...overrides,
  };
}

function nextId(items: { id: number }[]) {
  return Math.max(0, ...items.map((item) => item.id)) + 1;
}

function savePreset(server: FakeServer, id: number | null, body: Record<string, unknown>) {
  const name = String(body.name ?? "").trim();
  if (server.presets.some((preset) => preset.name === name && preset.id !== id)) {
    return json({ detail: `A preset named '${name}' already exists` }, 409);
  }
  const existing = server.presets.find((preset) => preset.id === id);
  const saved = makePreset({
    ...existing,
    ...(body as Partial<Preset>),
    id: id ?? nextId(server.presets),
  });
  if (saved.is_default) {
    server.presets = server.presets.map((preset) =>
      preset.kind === saved.kind ? { ...preset, is_default: false } : preset,
    );
  }
  server.presets = [...server.presets.filter((preset) => preset.id !== id), saved];
  return json(saved, id === null ? 201 : 200);
}

function saveCookieFile(server: FakeServer, id: number | null, body: Record<string, unknown>) {
  const content = String(body.content ?? "");
  if (!content.includes("\t")) {
    return json({ detail: "Line 1 isn't in Netscape cookies.txt format." }, 422);
  }
  const lines = content.split("\n").filter((line) => line.includes("\t"));
  const saved = makeCookieFile({
    id: id ?? nextId(server.cookieFiles),
    name: String(body.name),
    cookie_count: lines.length,
    domains: [...new Set(lines.map((line) => line.split("\t")[0]!.replace(/^\./, "")))],
  });
  server.cookieFiles = [...server.cookieFiles.filter((file) => file.id !== id), saved];
  return json(saved, id === null ? 201 : 200);
}

function checkCookieFile(body: Record<string, unknown>) {
  const url = String(body.url ?? "");
  if (url.includes("fail")) {
    return json({ ok: false, message: "[fake] Sign in to confirm you're not a bot" });
  }
  return json({ ok: true, message: "Opened “Members video” with these cookies." });
}

function saveSettings(server: FakeServer, body: Record<string, unknown>) {
  if (!String(body.download_dir).startsWith("/")) {
    return json({ detail: "Download folder must be an absolute path." }, 422);
  }
  server.settings = body as FakeServer["settings"];
  return json(server.settings);
}

function byName(a: { name: string }, b: { name: string }) {
  return a.name.localeCompare(b.name);
}

export const libraryRoutes: Route[] = [
  { method: "GET", path: /^\/api\/options\/schema$/, handle: () => json(FAKE_SCHEMA) },
  {
    method: "GET",
    path: /^\/api\/presets$/,
    handle: (server) => json(server.presets.toSorted(byName)),
  },
  { method: "POST", path: /^\/api\/presets$/, handle: (s, { body }) => savePreset(s, null, body) },
  {
    method: "PUT",
    path: /^\/api\/presets\/(\d+)$/,
    handle: (server, { body, params }) => savePreset(server, Number(params[0]), body),
  },
  {
    method: "DELETE",
    path: /^\/api\/presets\/(\d+)$/,
    handle: (server, { params }) => {
      server.presets = server.presets.filter((preset) => preset.id !== Number(params[0]));
      return noContent();
    },
  },
  {
    method: "GET",
    path: /^\/api\/cookies$/,
    handle: (server) => json(server.cookieFiles.toSorted(byName)),
  },
  {
    method: "POST",
    path: /^\/api\/cookies$/,
    handle: (server, { body }) => saveCookieFile(server, null, body),
  },
  {
    method: "PUT",
    path: /^\/api\/cookies\/(\d+)$/,
    handle: (server, { body, params }) => saveCookieFile(server, Number(params[0]), body),
  },
  {
    method: "DELETE",
    path: /^\/api\/cookies\/(\d+)$/,
    handle: (server, { params }) => {
      server.cookieFiles = server.cookieFiles.filter((file) => file.id !== Number(params[0]));
      return noContent();
    },
  },
  {
    method: "POST",
    path: /^\/api\/cookies\/(\d+)\/check$/,
    handle: (_s, { body }) => checkCookieFile(body),
  },
  {
    method: "GET",
    path: /^\/api\/folders$/,
    handle: (server, { query }) =>
      json({ folders: server.folders[query.get("parent") ?? ""] ?? [] }),
  },
  { method: "GET", path: /^\/api\/settings$/, handle: (server) => json(server.settings) },
  { method: "PUT", path: /^\/api\/settings$/, handle: (s, { body }) => saveSettings(s, body) },
];
