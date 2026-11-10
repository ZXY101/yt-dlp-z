// A guess at what a link points at, from its address alone, so the popup can show the right
// button at once. The server's link check replaces the guess 2–7 s later. Sites not listed
// here are "unknown" until the check answers.

export type LinkGuess =
  "unsupported" | "unknown" | "video" | "video-in-playlist" | "playlist" | "channel";

const YOUTUBE_HOSTS = new Set(["youtube.com", "m.youtube.com", "music.youtube.com"]);
const CHANNEL_PATH = /^\/(@[^/]+|channel\/[^/]+|c\/[^/]+|user\/[^/]+)(\/|$)/;
const VIDEO_PATH = /^\/(shorts|live|embed)\/[^/]+/;

function youtubeGuess(url: URL): LinkGuess {
  const params = url.searchParams;
  if (url.pathname === "/watch" && params.has("v")) {
    return params.has("list") ? "video-in-playlist" : "video";
  }
  if (url.pathname === "/playlist" && params.has("list")) return "playlist";
  if (VIDEO_PATH.test(url.pathname)) return "video";
  if (CHANNEL_PATH.test(url.pathname)) return "channel";
  return "unknown";
}

function shortLinkGuess(url: URL): LinkGuess {
  if (url.pathname.length <= 1) return "unknown";
  return url.searchParams.has("list") ? "video-in-playlist" : "video";
}

function bareHost(url: URL): string {
  return url.hostname.toLowerCase().replace(/^www\./, "");
}

export function guessLink(address: string): LinkGuess {
  let url: URL;
  try {
    url = new URL(address);
  } catch {
    return "unsupported";
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") return "unsupported";
  const host = bareHost(url);
  if (YOUTUBE_HOSTS.has(host)) return youtubeGuess(url);
  if (host === "youtu.be") return shortLinkGuess(url);
  if (host === "vimeo.com" && /^\/\d+/.test(url.pathname)) return "video";
  return "unknown";
}

// Guesses that are whole lists: the menu never sends these, the popup asks first.
export function isWholeList(guess: LinkGuess): boolean {
  return guess === "playlist" || guess === "channel";
}

// Pages "check links ahead" looks at: single videos, also opened from a playlist.
export function isVideoPage(address: string): boolean {
  const guess = guessLink(address);
  return guess === "video" || guess === "video-in-playlist";
}
