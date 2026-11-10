import { ServerProblem } from "../lib/problems.ts";
import {
  getPresets,
  jobsForLink,
  type LinkJobsRequest,
  probeLink,
  sendLink,
  type ProbeRequest,
  type SendRequest,
} from "../lib/server.ts";
import { loadConnection, savePresets, type Connection } from "../lib/settings.ts";
import type { LinkJob, MediaInfo, Preset, SentLink } from "../lib/types.ts";

async function requireConnection(): Promise<Connection> {
  const connection = await loadConnection();
  if (!connection) {
    throw new ServerProblem("not-set-up", "Set up the extension with your server's address.");
  }
  return connection;
}

// The popup may ask again while a check runs (reopened, or Download clicked): one request.
const probesInFlight = new Map<string, Promise<MediaInfo>>();

function probeKey(request: ProbeRequest): string {
  return JSON.stringify([request.url, request.cookieId, request.noPlaylist]);
}

export async function probe(request: ProbeRequest): Promise<MediaInfo> {
  const key = probeKey(request);
  const running = probesInFlight.get(key);
  if (running) return running;
  const connection = await requireConnection();
  const check = probeLink(connection, request).finally(() => probesInFlight.delete(key));
  probesInFlight.set(key, check);
  return check;
}

export async function send(request: SendRequest): Promise<SentLink> {
  return sendLink(await requireConnection(), request);
}

export async function refreshPresets(): Promise<Preset[]> {
  const presets = await getPresets(await requireConnection());
  await savePresets(presets);
  return presets;
}

export async function jobs(request: LinkJobsRequest): Promise<LinkJob[]> {
  return jobsForLink(await requireConnection(), request);
}
