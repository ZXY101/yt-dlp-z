import type { Job } from "@/features/downloads/types";

const UNITS = ["B", "KB", "MB", "GB", "TB"];
const SECONDS_PER_HOUR = 3600;
const SECONDS_PER_MINUTE = 60;

export function formatBytes(bytes: number) {
  let value = bytes;
  let unit = 0;
  while (value >= 1000 && unit < UNITS.length - 1) {
    value /= 1000;
    unit += 1;
  }
  const digits = unit === 0 || value >= 100 ? 0 : 1;
  return `${value.toFixed(digits)} ${UNITS[unit] ?? "B"}`;
}

export function formatDuration(totalSeconds: number) {
  const seconds = Math.max(0, Math.round(totalSeconds));
  const hours = Math.floor(seconds / SECONDS_PER_HOUR);
  const minutes = Math.floor((seconds % SECONDS_PER_HOUR) / SECONDS_PER_MINUTE);
  const paddedSeconds = String(seconds % SECONDS_PER_MINUTE).padStart(2, "0");
  if (hours === 0) {
    return `${minutes}:${paddedSeconds}`;
  }
  return `${hours}:${String(minutes).padStart(2, "0")}:${paddedSeconds}`;
}

function sizeText(job: Job) {
  if (job.downloaded_bytes == null) {
    return null;
  }
  const downloaded = formatBytes(job.downloaded_bytes);
  return job.total_bytes ? `${downloaded} of ${formatBytes(job.total_bytes)}` : downloaded;
}

/** e.g. "42% · 12.3 MB of 30.0 MB · 2.1 MB/s · 0:08 left" */
export function describeProgress(job: Job) {
  const parts = [
    job.progress == null ? null : `${Math.floor(job.progress)}%`,
    sizeText(job),
    job.speed == null ? null : `${formatBytes(job.speed)}/s`,
    job.eta == null ? null : `${formatDuration(job.eta)} left`,
  ];
  return parts.filter(Boolean).join(" · ") || "Starting…";
}
