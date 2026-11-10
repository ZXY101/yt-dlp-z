// How a link's existing job reads in the popup. Pure functions, tested without a browser.
import type { LinkJob } from "../lib/types.ts";

const ACTIVE = new Set(["scheduled", "queued", "running"]);

export function isActive(job: LinkJob | null): boolean {
  return job !== null && ACTIVE.has(job.status);
}

export function formatBytes(bytes: number): string {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1000 && unit < units.length - 1) {
    value /= 1000;
    unit += 1;
  }
  const digits = value >= 100 || unit === 0 ? 0 : 1;
  return `${value.toFixed(digits)} ${units[unit]}`;
}

function formatEta(seconds: number): string {
  if (seconds < 60) return `${seconds}s left`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}:${String(seconds % 60).padStart(2, "0")} left`;
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m left`;
}

function formatWhen(iso: string): string {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export interface JobView {
  status: string;
  detail: string;
  // 0–1 for a progress bar; null hides it, undefined shows a busy bar.
  fraction: number | null | undefined;
}

function runningView(job: LinkJob): JobView {
  const done = job.downloaded_bytes ? formatBytes(job.downloaded_bytes) : "";
  if (job.kind === "live") {
    const part = job.part && job.part > 1 ? ` (part ${job.part})` : "";
    return { status: `Recording${part}`, detail: done && `${done} so far`, fraction: undefined };
  }
  // The server sends progress as a percentage, 0–100.
  const percent = job.progress === null ? "" : ` ${Math.floor(job.progress)}%`;
  const details = [
    job.speed ? `${formatBytes(job.speed)}/s` : "",
    job.eta ? formatEta(job.eta) : "",
  ];
  const detail = details.filter(Boolean).join(" · ");
  return {
    status: `Downloading${percent}`,
    detail,
    fraction: job.progress === null ? undefined : job.progress / 100,
  };
}

function whenOrEmpty(iso: string | null, prefix = ""): string {
  return iso ? `${prefix}${formatWhen(iso)}` : "";
}

const VIEWS: Record<LinkJob["status"], (job: LinkJob) => JobView> = {
  running: runningView,
  queued: () => ({ status: "Waiting in the queue", detail: "", fraction: undefined }),
  scheduled: (job) => ({
    status: "Recording scheduled",
    detail: whenOrEmpty(job.scheduled_at, "Starts "),
    fraction: null,
  }),
  completed: (job) => ({
    status: job.kind === "live" ? "Recorded ✓" : "Downloaded ✓",
    detail: whenOrEmpty(job.finished_at),
    fraction: null,
  }),
  failed: (job) => ({
    status: "Last try failed",
    detail: friendlyError(job.error ?? ""),
    fraction: null,
  }),
  cancelled: (job) => ({
    status: "Cancelled",
    detail: whenOrEmpty(job.finished_at),
    fraction: null,
  }),
};

export function describeJob(job: LinkJob): JobView {
  return VIEWS[job.status](job);
}

const MAX_ERROR_LENGTH = 180;

// yt-dlp's errors can run to several lines with the whole link in them.
export function friendlyError(message: string): string {
  const text = message.replace(/^ERROR:\s*/i, "").trim();
  if (/unsupported url/i.test(text)) return "yt-dlp doesn't support this page.";
  if (text.length <= MAX_ERROR_LENGTH) return text;
  return `${text.slice(0, MAX_ERROR_LENGTH).trimEnd()}…`;
}
