import type { components } from "@/api/generated/schema";
import type { AuthStatus } from "@/features/auth/types";
import type { Job } from "@/features/downloads/types";

export interface FakeServer {
  status: AuthStatus;
  /** When set, every request fails with this HTTP status. */
  failWith: number | null;
  requests: string[];
  jobs: Job[];
  nextJobId: number;
  logs: Record<number, string>;
  system: components["schemas"]["SystemInfo"];
  presets: components["schemas"]["PresetOut"][];
  cookieFiles: components["schemas"]["CookieFileOut"][];
  settings: components["schemas"]["AppSettings"];
  subscriptions: components["schemas"]["SubscriptionOut"][];
  /** Recent videos by subscription id. */
  videos: Record<number, components["schemas"]["VideoOut"][]>;
  ytdlp: components["schemas"]["YtdlpInfo"];
  /** Makes the next yt-dlp update fail. */
  ytdlpUpdateFails: boolean;
  // Jobs removed with "Delete files".
  deletedJobFiles: number[];
  notifications: components["schemas"]["NotificationSettingsOut"];
  apiTokens: components["schemas"]["ApiTokenOut"][];
  /** The saved ntfy token, never sent back by the real server. */
  notificationToken: string;
  /** Test messages sent, and the error the next one gets (null = it works). */
  sentTests: components["schemas"]["NotificationSettingsIn"][];
  testError: string | null;
  pot: components["schemas"]["PotProviderInfo"];
  // Version the fake provider answers with; null acts like an unreachable one.
  potServerVersion: string | null;
  proxies: components["schemas"]["ProxyOut"][];
  proxySettings: components["schemas"]["ProxySettings"];
  /** Folder suggestions by parent path. */
  folders: Record<string, string[]>;
}

interface RouteRequest {
  body: Record<string, unknown>;
  /** Captured groups of the route's path pattern. */
  params: string[];
  query: URLSearchParams;
}

export interface Route {
  method: string;
  path: RegExp;
  handle: (server: FakeServer, request: RouteRequest) => Response;
}

export function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export function noContent() {
  return new Response(null, { status: 204 });
}
