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
