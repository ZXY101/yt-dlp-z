import { ServerProblem } from "./problems.ts";
import type { Connection } from "./settings.ts";
import type { Health, MediaInfo, Preset, SentLink } from "./types.ts";
import { isAtLeast, MIN_SERVER_VERSION } from "./version.ts";

const QUICK_TIMEOUT_MS = 15_000;
// A link check can take ~7 s on a cold server, much longer for a slow site.
const PROBE_TIMEOUT_MS = 90_000;

interface CallOptions {
  method?: "GET" | "POST";
  body?: unknown;
  timeoutMs?: number;
}

function requestHeaders(connection: Connection, hasBody: boolean): Headers {
  const headers = new Headers({ Accept: "application/json" });
  for (const { name, value } of connection.headers) headers.set(name, value);
  if (connection.token) headers.set("Authorization", `Bearer ${connection.token}`);
  if (hasBody) headers.set("Content-Type", "application/json");
  return headers;
}

async function detailOf(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((item: { msg?: string }) => item.msg ?? "").join("; ");
    }
  } catch {
    // Not JSON: fall back to the status line.
  }
  return `${response.status} ${response.statusText}`.trim();
}

function looksLikeLoginPage(response: Response): boolean {
  // A login proxy answers with a redirect or its own HTML page instead of our JSON.
  if (response.type === "opaqueredirect") return true;
  const type = response.headers.get("Content-Type") ?? "";
  return type.includes("text/html");
}

async function problemFor(response: Response, connection: Connection): Promise<ServerProblem> {
  const detail = await detailOf(response);
  if (response.status === 401 && !connection.token) {
    return new ServerProblem("needs-token", "This server needs an API token.");
  }
  if (response.status === 401) {
    return new ServerProblem("bad-token", "The server didn't accept the token. Was it revoked?");
  }
  if (response.status === 403) return new ServerProblem("send-only", detail);
  if (response.status === 404 || response.status === 405) {
    return new ServerProblem("too-old", `Update yt-dlp-z to ${MIN_SERVER_VERSION} or newer.`);
  }
  if (response.status === 422) return new ServerProblem("rejected", detail);
  return new ServerProblem("server-error", `The server answered: ${detail}`);
}

async function send(connection: Connection, path: string, options: CallOptions): Promise<Response> {
  const hasBody = options.body !== undefined;
  try {
    return await fetch(`${connection.address}${path}`, {
      method: options.method ?? "GET",
      headers: requestHeaders(connection, hasBody),
      body: hasBody ? JSON.stringify(options.body) : undefined,
      redirect: "manual",
      credentials: "omit",
      signal: AbortSignal.timeout(options.timeoutMs ?? QUICK_TIMEOUT_MS),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new ServerProblem("timeout", "The server took too long to answer.");
    }
    throw new ServerProblem("unreachable", `Can't reach ${connection.address}.`);
  }
}

async function call<T>(connection: Connection, path: string, options: CallOptions = {}) {
  const response = await send(connection, path, options);
  if (looksLikeLoginPage(response)) {
    throw new ServerProblem(
      "login-page",
      "A login page answered instead of yt-dlp-z. Add a header your proxy accepts, " +
        "or let /api/ through without its login.",
    );
  }
  if (!response.ok) throw await problemFor(response, connection);
  return (await response.json()) as T;
}

export async function getHealth(connection: Connection): Promise<Health> {
  const health = await call<Health>(connection, "/api/health");
  if (!isAtLeast(health.version, MIN_SERVER_VERSION)) {
    throw new ServerProblem(
      "too-old",
      `This server runs yt-dlp-z ${health.version}. Update it to ${MIN_SERVER_VERSION} or newer.`,
    );
  }
  return health;
}

export function getPresets(connection: Connection): Promise<Preset[]> {
  return call<Preset[]>(connection, "/api/presets");
}

export interface ProbeRequest {
  url: string;
  cookieId: number | null;
  noPlaylist: boolean;
}

export function probeLink(connection: Connection, request: ProbeRequest): Promise<MediaInfo> {
  const body = { url: request.url, cookie_id: request.cookieId, no_playlist: request.noPlaylist };
  return call<MediaInfo>(connection, "/api/media/probe", {
    method: "POST",
    body,
    timeoutMs: PROBE_TIMEOUT_MS,
  });
}

export interface SendRequest {
  url: string;
  presetId: number | null;
  wholePlaylist: boolean;
}

export function sendLink(connection: Connection, request: SendRequest): Promise<SentLink> {
  const body = {
    url: request.url,
    preset_id: request.presetId,
    whole_playlist: request.wholePlaylist,
  };
  return call<SentLink>(connection, "/api/jobs/send", {
    method: "POST",
    body,
    timeoutMs: PROBE_TIMEOUT_MS,
  });
}
