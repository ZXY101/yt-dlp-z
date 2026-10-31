import type { RecordingSettings } from "@/features/presets";

const SECONDS_PER_HOUR = 3600;
const SECONDS_PER_MINUTE = 60;

export interface RecordingPlan {
  fromStart: boolean;
  partHours: number | null;
  maxHours: number | null;
}

/** Seconds since the stream went live. */
export function liveForSeconds(liveSince: string, now: number) {
  return (now - new Date(liveSince).getTime()) / 1000;
}

/** What a preset's recording settings mean for this stream; mirrors the backend's
 * plan_recording, which subscriptions use. `liveSince`: null for upcoming streams. */
export function planRecording(
  recording: RecordingSettings,
  liveSince: string | null,
  now: number,
): RecordingPlan {
  const plan = { fromStart: true, partHours: recording.part_hours, maxHours: recording.max_hours };
  const limit = recording.from_start_max_hours;
  if (liveSince === null || limit === null) {
    return plan;
  }
  if (liveForSeconds(liveSince, now) <= limit * SECONDS_PER_HOUR) {
    return plan;
  }
  if (recording.long_streams === "first_hours") {
    return { ...plan, maxHours: Math.min(plan.maxHours ?? limit, limit) };
  }
  return { ...plan, fromStart: false };
}

/** e.g. "40 min", "3 h 20 min". */
export function formatLiveFor(seconds: number) {
  const minutes = Math.max(1, Math.floor(seconds / SECONDS_PER_MINUTE));
  const hours = Math.floor(minutes / SECONDS_PER_MINUTE);
  if (hours === 0) {
    return `${minutes} min`;
  }
  return `${hours} h ${minutes % SECONDS_PER_MINUTE} min`;
}
