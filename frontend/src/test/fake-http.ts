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
}

interface RouteRequest {
  body: Record<string, unknown>;
  /** Captured groups of the route's path pattern. */
  params: string[];
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
