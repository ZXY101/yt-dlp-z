import type { MediaInfo } from "@/features/downloads/types";
import { type Route, json } from "@/test/fake-http";

/** Answers like the backend's link check with the fake yt-dlp; the URL picks the media. */
function media(overrides: Partial<MediaInfo>): MediaInfo {
  return {
    kind: "video",
    title: "Fake video",
    uploader: "Fake channel",
    thumbnail: null,
    site: "youtube.com",
    duration: 300,
    entry_count: null,
    starts_at: null,
    live_since: null,
    members_only: false,
    ...overrides,
  };
}

const MEMBERS_MESSAGE =
  "This is for channel members only. Choose a cookies file from a member's account.";

function probe(body: Record<string, unknown>) {
  const url = String(body.url);
  if (url.includes("broken")) {
    return json({ detail: "This video is unavailable" }, 422);
  }
  if (url.includes("members") && body.cookie_id == null) {
    return json({ detail: MEMBERS_MESSAGE }, 422);
  }
  if (url.includes("list=") && !body.no_playlist) {
    return json(media({ kind: "playlist", title: "Fake playlist", entry_count: 24 }));
  }
  if (url.includes("/@")) {
    return json(media({ kind: "channel", title: "Fake channel", entry_count: 3 }));
  }
  if (url.includes("upcoming")) {
    const startsAt = "2100-01-01T00:00:00+00:00";
    return json(media({ kind: "upcoming", starts_at: startsAt }));
  }
  if (url.includes("live")) {
    // "old" streams have been live for 10 hours, the rest for 1.
    const hours = url.includes("old") ? 10 : 1;
    const liveSince = new Date(Date.now() - hours * 3600 * 1000).toISOString();
    return json(media({ kind: "live", duration: null, live_since: liveSince }));
  }
  return json(media({ members_only: url.includes("members") }));
}

export const mediaRoutes: Route[] = [
  { method: "POST", path: /^\/api\/media\/probe$/, handle: (_server, { body }) => probe(body) },
];
