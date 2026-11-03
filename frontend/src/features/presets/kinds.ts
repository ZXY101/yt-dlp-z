import type { Preset, PresetKind, RecordingSettings } from "@/features/presets/types";

export const PRESET_KIND_LABELS: Record<PresetKind, string> = {
  any: "Any link",
  video: "Videos",
  playlist: "Playlists and channels",
  live: "Live streams",
};

// A week; longer values are almost certainly typos.
export const MAX_RECORDING_HOURS = 168;

/** Before the backend's migration created one, recordings used these. */
export const DEFAULT_RECORDING: RecordingSettings = {
  part_hours: 6,
  max_hours: null,
  from_start_max_hours: 6,
  long_streams: "from_now",
  vod_after_hours: null,
  vod_replace: false,
};

type MediaKind = "video" | "playlist" | "channel" | "live" | "upcoming";

const KIND_OF_MEDIA: Record<MediaKind, PresetKind> = {
  video: "video",
  playlist: "playlist",
  channel: "playlist",
  live: "live",
  upcoming: "live",
};

export function presetKindFor(mediaKind: MediaKind): PresetKind {
  return KIND_OF_MEDIA[mediaKind];
}

/** The default preset for this kind of link, else the default for any link. */
export function defaultPresetFor(presets: Preset[], kind: PresetKind) {
  const forKind = presets.find((preset) => preset.kind === kind && preset.is_default);
  return forKind ?? presets.find((preset) => preset.kind === "any" && preset.is_default);
}

function matchRank(preset: Preset, kind: PresetKind) {
  if (preset.kind === kind) {
    return 0;
  }
  return preset.kind === "any" ? 1 : 2;
}

/** Presets made for this kind of link first, then those for any link, then the rest. */
export function sortForKind(presets: Preset[], kind: PresetKind) {
  return presets.toSorted((a, b) => matchRank(a, kind) - matchRank(b, kind));
}

/** The recording settings a live stream starts with: the preset's, else the default
 * live-stream preset's. */
export function recordingFor(preset: Preset | undefined, presets: Preset[]) {
  const fallback = defaultPresetFor(presets, "live")?.recording;
  return preset?.recording ?? fallback ?? DEFAULT_RECORDING;
}
