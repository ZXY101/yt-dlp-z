import { sendsTokenInTheClear } from "../lib/address.ts";
import { getHealth, getPresets } from "../lib/server.ts";
import type { Connection } from "../lib/settings.ts";
import type { Preset } from "../lib/types.ts";

export interface TestResult {
  version: string;
  presets: Preset[];
  warnings: string[];
}

function warningsFor(connection: Connection): string[] {
  if (!connection.token || !sendsTokenInTheClear(connection.address)) return [];
  return [
    "This address uses plain HTTP over the internet, so the token can be read on the way. " +
      "Use HTTPS, or a private address (LAN, Tailscale).",
  ];
}

// Throws a ServerProblem naming the first thing that's wrong.
export async function testConnection(connection: Connection): Promise<TestResult> {
  const health = await getHealth(connection);
  const presets = await getPresets(connection);
  return { version: health.version, presets, warnings: warningsFor(connection) };
}
