import type { NotificationSettingsIn } from "@/features/settings/types";
import { type FakeServer, type Route, json, noContent } from "@/test/fake-http";

export function makeNotifications() {
  return {
    notifications: {
      server: "https://ntfy.sh",
      topic: "",
      events: [
        "recording_started" as const,
        "download_finished" as const,
        "download_failed" as const,
        "problems" as const,
      ],
      has_token: false,
    },
    notificationToken: "",
    sentTests: [],
    testError: null,
  };
}

function save(server: FakeServer, body: NotificationSettingsIn) {
  if (body.token !== null && body.token !== undefined) {
    server.notificationToken = body.token;
  }
  server.notifications = {
    server: body.server ?? "https://ntfy.sh",
    topic: body.topic ?? "",
    events: body.events ?? [],
    has_token: server.notificationToken !== "",
  };
}

export const notificationRoutes: Route[] = [
  {
    method: "GET",
    path: /^\/api\/notifications$/,
    handle: (server) => json(server.notifications),
  },
  {
    method: "PUT",
    path: /^\/api\/notifications$/,
    handle: (server, { body }) => {
      save(server, body as NotificationSettingsIn);
      return json(server.notifications);
    },
  },
  {
    method: "POST",
    path: /^\/api\/notifications\/test$/,
    handle: (server, { body }) => {
      if (server.testError) {
        return json({ detail: server.testError }, 502);
      }
      server.sentTests.push(body as NotificationSettingsIn);
      return noContent();
    },
  },
];
