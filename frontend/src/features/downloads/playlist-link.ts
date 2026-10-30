/**
 * What a link points at, as far as playlists go:
 * - "video-in-playlist": a video opened from inside a playlist (`watch?v=…&list=…`)
 * - "playlist" / "channel": yt-dlp downloads every video in it
 * - undefined: a single video, or a link yt-dlp-z doesn't recognise
 */
export type PlaylistLinkKind = "video-in-playlist" | "playlist" | "channel";

const YOUTUBE_HOSTS = new Set([
  "youtube.com",
  "www.youtube.com",
  "m.youtube.com",
  "music.youtube.com",
]);

// Channel pages: /@handle, /channel/UC…, /c/name, /user/name, and their tabs.
const CHANNEL_PATH = /^\/(@[^/]+|channel\/[^/]+|c\/[^/]+|user\/[^/]+)(\/|$)/;

export function playlistLinkKind(url: string): PlaylistLinkKind | undefined {
  const link = parseUrl(url.trim());
  if (!link) {
    return undefined;
  }
  if (link.hostname === "youtu.be") {
    return link.searchParams.has("list") ? "video-in-playlist" : undefined;
  }
  if (!YOUTUBE_HOSTS.has(link.hostname)) {
    return undefined;
  }
  return youtubeKind(link);
}

function youtubeKind(link: URL): PlaylistLinkKind | undefined {
  const hasList = link.searchParams.has("list");
  if (link.pathname === "/watch") {
    return hasList && link.searchParams.has("v") ? "video-in-playlist" : undefined;
  }
  if (link.pathname === "/playlist") {
    return hasList ? "playlist" : undefined;
  }
  if (CHANNEL_PATH.test(link.pathname)) {
    return "channel";
  }
  return undefined;
}

function parseUrl(url: string) {
  try {
    return new URL(url);
  } catch {
    return undefined;
  }
}
