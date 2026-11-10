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

export interface SentLink {
  job: { id: number; title: string | null; kind: string };
  preset: string | null;
}

export interface Health {
  status: string;
  version: string;
}
