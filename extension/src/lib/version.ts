// The first server release with send-only tokens and POST /api/jobs/send.
export const MIN_SERVER_VERSION = "0.1.6";

function parts(version: string): number[] {
  return version
    .replace(/^v/, "")
    .split(/[.+-]/)
    .slice(0, 3)
    .map((part) => Number.parseInt(part, 10) || 0);
}

export function isAtLeast(version: string, minimum: string): boolean {
  const have = parts(version);
  const need = parts(minimum);
  for (let index = 0; index < 3; index += 1) {
    const difference = (have[index] ?? 0) - (need[index] ?? 0);
    if (difference !== 0) return difference > 0;
  }
  return true;
}
