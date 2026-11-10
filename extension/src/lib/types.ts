// The parts of the yt-dlp-z API the extension reads. The server is versioned on its own,
// so only fields that every supported server version sends are listed.

type PresetKind = "any" | "video" | "playlist" | "live";

export interface Preset {
  id: number;
  name: string;
  kind: PresetKind;
  is_default: boolean;
  cookie_id: number | null;
}

type MediaKind = "video" | "playlist" | "channel" | "live" | "upcoming";

export interface MediaInfo {
  kind: MediaKind;
  title: string | null;
  uploader: string | null;
  thumbnail: string | null;
  duration: number | null;
  entry_count: number | null;
  starts_at: string | null;
  members_only: boolean;
}

type JobStatus = "scheduled" | "queued" | "running" | "completed" | "failed" | "cancelled";

// A job's progress as POST /api/jobs/for-link returns it (server 0.1.7+).
export interface LinkJob {
  id: number;
  status: JobStatus;
  kind: "download" | "live";
  title: string | null;
  // Percent, 0–100.
  progress: number | null;
  downloaded_bytes: number | null;
  total_bytes: number | null;
  speed: number | null;
  eta: number | null;
  part: number | null;
  scheduled_at: string | null;
  error: string | null;
  created_at: string;
  finished_at: string | null;
}

export interface SentLink {
  job: LinkJob;
  preset: string | null;
  // Server 0.1.7+: the same link with the same settings was already queued or downloaded.
  existing?: boolean;
}

export interface Health {
  status: string;
  version: string;
}
