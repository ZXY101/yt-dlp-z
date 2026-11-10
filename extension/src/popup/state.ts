// What the popup shows and sends, worked out from the link, the check and the user's choices.
// Pure functions, so the rules can be tested without a browser.
import { isWholeList, type LinkGuess } from "../lib/link-guess.ts";
import type { ProbeRequest, SendRequest } from "../lib/server.ts";
import type { MediaInfo, Preset } from "../lib/types.ts";

export interface PopupState {
  url: string;
  guess: LinkGuess;
  // The server's answer for the current probe request, once it arrives.
  info: MediaInfo | null;
  // Only used for a video opened from a playlist: send the playlist instead.
  wholePlaylist: boolean;
  presetId: number | null;
  presets: Preset[];
}

function chosenPreset(state: PopupState): Preset | undefined {
  return state.presets.find((preset) => preset.id === state.presetId);
}

function isList(state: PopupState): boolean {
  if (state.guess === "video-in-playlist") return state.wholePlaylist;
  if (state.info) return state.info.kind === "playlist" || state.info.kind === "channel";
  return isWholeList(state.guess);
}

export function probeRequestFor(state: PopupState): ProbeRequest {
  return {
    url: state.url,
    // The same cookies the send will use, so the server's cached check is reused.
    cookieId: chosenPreset(state)?.cookie_id ?? null,
    noPlaylist: state.guess === "video-in-playlist" && !state.wholePlaylist,
  };
}

export function sendRequestFor(state: PopupState): SendRequest {
  return { url: state.url, presetId: state.presetId, wholePlaylist: isList(state) };
}

export function buttonLabel(state: PopupState): string {
  if (state.info?.kind === "live") return "Record";
  if (state.info?.kind === "upcoming") return "Schedule recording";
  if (!isList(state)) return "Download";
  const count = state.info?.entry_count;
  return count ? `Download ${count} videos` : "Download all videos";
}

const GUESS_LABELS: Record<LinkGuess, string> = {
  unsupported: "This page can't be sent",
  unknown: "Link",
  video: "Video",
  "video-in-playlist": "Video in a playlist",
  playlist: "Playlist",
  channel: "Channel",
};

export function guessLabel(guess: LinkGuess): string {
  return GUESS_LABELS[guess];
}

export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const rest = String(Math.floor(seconds % 60)).padStart(2, "0");
  if (hours === 0) return `${minutes}:${rest}`;
  return `${hours}:${String(minutes).padStart(2, "0")}:${rest}`;
}

function startsAt(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function kindParts(info: MediaInfo): string[] {
  if (info.kind === "live") return ["Live now"];
  if (info.kind === "upcoming") {
    return info.starts_at ? [`Starts ${startsAt(info.starts_at)}`] : ["Upcoming stream"];
  }
  if (info.kind === "video")
    return info.duration ? ["Video", formatDuration(info.duration)] : ["Video"];
  const name = info.kind === "channel" ? "Channel" : "Playlist";
  return info.entry_count ? [name, `${info.entry_count} videos`] : [name];
}

export function describeInfo(info: MediaInfo): string {
  const parts = kindParts(info);
  if (info.uploader) parts.push(info.uploader);
  if (info.members_only) parts.push("Members only");
  return parts.join(" · ");
}

export function presetLabel(preset: Preset): string {
  return preset.kind === "any" ? preset.name : `${preset.name} (${preset.kind})`;
}
