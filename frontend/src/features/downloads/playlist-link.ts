/**
 * Whether a link is a YouTube video opened from inside a playlist (`watch?v=…&list=…`).
 * yt-dlp downloads the whole playlist for those unless told otherwise, so the form asks.
 * Other playlists and channels are recognised by the link check (`useLinkCheck`).
 */
const YOUTUBE_HOSTS = new Set([
  "youtube.com",
  "www.youtube.com",
  "m.youtube.com",
  "music.youtube.com",
]);

export function isVideoInPlaylist(url: string) {
  const link = parseUrl(url.trim());
  if (!link?.searchParams.has("list")) {
    return false;
  }
  if (link.hostname === "youtu.be") {
    return true;
  }
  return (
    YOUTUBE_HOSTS.has(link.hostname) && link.pathname === "/watch" && link.searchParams.has("v")
  );
}

function parseUrl(url: string) {
  try {
    return new URL(url);
  } catch {
    return undefined;
  }
}
