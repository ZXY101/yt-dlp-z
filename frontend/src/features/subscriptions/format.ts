import type { Subscription, VideoState } from "@/features/subscriptions/types";

const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["year", 31_536_000],
  ["month", 2_592_000],
  ["day", 86_400],
  ["hour", 3600],
  ["minute", 60],
];
const relative = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

/** "5 minutes ago", "in 2 days"; anything under a minute is "just now". */
export function formatRelative(iso: string, now = Date.now()) {
  const seconds = Math.round((new Date(iso).getTime() - now) / 1000);
  for (const [unit, size] of UNITS) {
    if (Math.abs(seconds) >= size) {
      return relative.format(Math.trunc(seconds / size), unit);
    }
  }
  return "just now";
}

export function describeCheck(subscription: Subscription, now = Date.now()) {
  if (subscription.checking) {
    return "Checking now…";
  }
  if (!subscription.last_checked_at) {
    return "Not checked yet";
  }
  return `Checked ${formatRelative(subscription.last_checked_at, now)}`;
}

export const VIDEO_STATE_LABELS: Record<VideoState, string> = {
  queued: "Downloading",
  skipped: "Skipped",
  upcoming: "Recording scheduled",
  live: "Recording",
  failed: "Failed",
};
