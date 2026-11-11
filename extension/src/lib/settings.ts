import { ext } from "./browser.ts";
import type { Preset } from "./types.ts";

export interface Header {
  name: string;
  value: string;
}

export interface Connection {
  // The server's base address, e.g. "http://192.168.1.5:9742" (no trailing slash).
  address: string;
  // Empty for servers with AUTH_MODE=none.
  token: string;
  // Sent with every request, for proxies that accept a fixed credential.
  headers: Header[];
}

// Kept in storage.local, never storage.sync, so the token stays on this device.
interface Stored {
  connection?: Connection;
  presets?: Preset[];
  lastPresetId?: number | null;
  checkAhead?: boolean;
}

async function read<K extends keyof Stored>(key: K): Promise<Stored[K]> {
  const stored = (await ext.storage.local.get(key)) as Stored;
  return stored[key];
}

export async function loadConnection(): Promise<Connection | null> {
  return (await read("connection")) ?? null;
}

export async function saveConnection(connection: Connection): Promise<void> {
  await ext.storage.local.set({ connection });
}

export async function loadPresets(): Promise<Preset[]> {
  return (await read("presets")) ?? [];
}

export async function savePresets(presets: Preset[]): Promise<void> {
  await ext.storage.local.set({ presets });
}

// null: "Default for this kind of link".
export async function loadLastPresetId(): Promise<number | null> {
  return (await read("lastPresetId")) ?? null;
}

export async function saveLastPresetId(lastPresetId: number | null): Promise<void> {
  await ext.storage.local.set({ lastPresetId });
}

// Firefox 140+ (Android 142+) also has data collection permissions, which @types/chrome lacks.
export interface Permissions extends chrome.permissions.Permissions {
  data_collection?: string[];
}

// Firefox's built-in data consent is there when getAll() reports a data_collection list.
export function hasDataConsent(granted: Permissions): boolean {
  return Array.isArray(granted.data_collection);
}

// What "check links ahead" needs: "tabs" to see tab addresses and, where the browser has data
// consent, "browsingActivity", because it sends the pages you stay on to your server without
// a click. The manifest lists both as optional, so nothing is asked at install.
export function checkAheadPermissions(dataConsent: boolean): Permissions {
  const tabs: Permissions = { permissions: ["tabs"] };
  return dataConsent ? { ...tabs, data_collection: ["browsingActivity"] } : tabs;
}

export async function checkAheadRequest(): Promise<Permissions> {
  return checkAheadPermissions(hasDataConsent(await ext.permissions.getAll()));
}

// Off unless the user switches it on: it sends every video page they open to their server.
export async function loadCheckAhead(): Promise<boolean> {
  return (await read("checkAhead")) ?? false;
}

export async function saveCheckAhead(checkAhead: boolean): Promise<void> {
  await ext.storage.local.set({ checkAhead });
}
