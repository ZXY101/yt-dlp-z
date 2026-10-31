import type { components } from "@/api/generated/schema";
import { type FakeServer, type Route, json, noContent } from "@/test/fake-http";

type Subscription = components["schemas"]["SubscriptionOut"];
type Video = components["schemas"]["VideoOut"];

const NOW = "2026-10-30T10:00:00+00:00";

export function makeSubscription(overrides: Partial<Subscription> = {}): Subscription {
  return {
    id: 1,
    channel_id: "UCdemo",
    name: "Demo channel",
    url: "https://www.youtube.com/channel/UCdemo",
    preset_id: null,
    stream_preset_id: null,
    cookie_id: null,
    output_dir: null,
    filters: { content_types: ["video"], include_members_only: false },
    poll_minutes: 10,
    enabled: true,
    backfill: 0,
    last_checked_at: null,
    last_error: null,
    created_at: NOW,
    checking: false,
    ...overrides,
  };
}

export function makeVideo(overrides: Partial<Video> = {}): Video {
  return {
    id: 1,
    video_id: "abc",
    title: "A video",
    published_at: NOW,
    state: "queued",
    reason: null,
    live_status: "not_live",
    release_at: null,
    job_id: 1,
    updated_at: NOW,
    ...overrides,
  };
}

function find(server: FakeServer, params: string[]) {
  return server.subscriptions.find((item) => item.id === Number(params[0]));
}

function notFound() {
  return json({ detail: "Subscription not found" }, 404);
}

function create(server: FakeServer, body: Record<string, unknown>) {
  const channel = String(body.channel);
  if (channel.includes("fail")) {
    return json({ detail: "Couldn't open that channel: [fake] This channel does not exist" }, 422);
  }
  const id = Math.max(0, ...server.subscriptions.map((item) => item.id)) + 1;
  const name = `Fake ${channel.replace(/^.*@/, "")}`;
  const { channel: _, ...fields } = body;
  const created = makeSubscription({ ...(fields as Partial<Subscription>), id, name });
  server.subscriptions = [...server.subscriptions, created];
  return json(created, 201);
}

function update(server: FakeServer, params: string[], body: Record<string, unknown>) {
  const existing = find(server, params);
  if (!existing) {
    return notFound();
  }
  const saved = { ...existing, ...(body as Partial<Subscription>) };
  server.subscriptions = server.subscriptions.map((item) => (item.id === saved.id ? saved : item));
  return json(saved);
}

function check(server: FakeServer, params: string[]) {
  const existing = find(server, params);
  if (!existing) {
    return notFound();
  }
  // Checks finish instantly here; the E2E suite covers the real background check.
  const checked = { ...existing, last_checked_at: new Date().toISOString() };
  server.subscriptions = server.subscriptions.map((item) =>
    item.id === checked.id ? checked : item,
  );
  return json(checked, 202);
}

export const subscriptionRoutes: Route[] = [
  { method: "GET", path: /^\/api\/subscriptions$/, handle: (s) => json(s.subscriptions) },
  { method: "POST", path: /^\/api\/subscriptions$/, handle: (s, { body }) => create(s, body) },
  {
    method: "PUT",
    path: /^\/api\/subscriptions\/(\d+)$/,
    handle: (s, { params, body }) => update(s, params, body),
  },
  {
    method: "DELETE",
    path: /^\/api\/subscriptions\/(\d+)$/,
    handle: (server, { params }) => {
      server.subscriptions = server.subscriptions.filter((item) => item.id !== Number(params[0]));
      return noContent();
    },
  },
  {
    method: "POST",
    path: /^\/api\/subscriptions\/(\d+)\/check$/,
    handle: (s, { params }) => check(s, params),
  },
  {
    method: "GET",
    path: /^\/api\/subscriptions\/(\d+)\/videos$/,
    handle: (server, { params }) => json(server.videos[Number(params[0])] ?? []),
  },
];
