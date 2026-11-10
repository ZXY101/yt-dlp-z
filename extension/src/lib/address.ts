// Turning what the user typed into a server address, and judging how safe it is to use.

export function normalizeAddress(input: string): string {
  const trimmed = input.trim();
  const withScheme = /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`;
  const url = new URL(withScheme);
  // Keep a path: the server may sit under a sub-path behind a reverse proxy.
  const path = url.pathname.replace(/\/+$/, "");
  return `${url.protocol}//${url.host}${path}`;
}

// The host permission to ask for: this one server, nothing else.
export function originPattern(address: string): string {
  const url = new URL(address);
  return `${url.protocol}//${url.hostname}/*`;
}

const PRIVATE_SUFFIXES = [".local", ".lan", ".home", ".internal", ".home.arpa", ".ts.net"];

// [first octet, lowest second octet, highest second octet]
const PRIVATE_IPV4_RANGES: [number, number, number][] = [
  [10, 0, 255],
  [127, 0, 255],
  [172, 16, 31],
  [192, 168, 168],
  // 100.64.0.0/10: carrier-grade NAT, which Tailscale uses.
  [100, 64, 127],
];

function isPrivateIpv4(host: string): boolean {
  if (!/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) return false;
  const [a = -1, b = -1] = host.split(".").map(Number);
  return PRIVATE_IPV4_RANGES.some(([first, low, high]) => a === first && b >= low && b <= high);
}

function isPrivateIpv6(host: string): boolean {
  const bare = host.replace(/^\[|\]$/g, "").toLowerCase();
  return bare === "::1" || /^f[cd]/.test(bare) || bare.startsWith("fe80:");
}

export function isPrivateHost(hostname: string): boolean {
  const host = hostname.toLowerCase();
  if (host.startsWith("[")) return isPrivateIpv6(host);
  // A single-label name ("nas") only resolves on a local network.
  if (!host.includes(".")) return true;
  if (PRIVATE_SUFFIXES.some((suffix) => host.endsWith(suffix))) return true;
  return isPrivateIpv4(host);
}

// A token sent this way can be read by anyone on the path to the server.
export function sendsTokenInTheClear(address: string): boolean {
  const url = new URL(address);
  return url.protocol === "http:" && !isPrivateHost(url.hostname);
}
