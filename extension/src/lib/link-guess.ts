// A guess at what a link points at, from its address alone, so the popup can show the right
// button at once. The server's link check replaces the guess 2–7 s later. Sites not listed
// here are "unknown" until the check answers.

export type LinkGuess =
  // Browser and extension pages: not web addresses at all.
  | "unsupported"
  // Sites and pages that clearly hold no video (search, mail, YouTube's home feed).
  | "not-media"
  | "unknown"
  | "video"
  | "video-in-playlist"
  | "playlist"
  | "channel";

const YOUTUBE_HOSTS = new Set(["youtube.com", "m.youtube.com", "music.youtube.com"]);
const CHANNEL_PATH = /^\/(@[^/]+|channel\/[^/]+|c\/[^/]+|user\/[^/]+)(\/|$)/;
const VIDEO_PATH = /^\/(shorts|live|embed)\/[^/]+/;
// YouTube pages that list or manage things rather than show one video, playlist or channel.
const YOUTUBE_NON_MEDIA = /^\/($|feed|results|account|premium|reporthistory|upload|signin|logout)/;
// Whole sites yt-dlp has nothing to download from. Kept short and obvious on purpose:
// yt-dlp's generic extractor finds embedded videos on most other pages.
const NON_MEDIA_HOSTS = new Set([
  "google.com",
  "bing.com",
  "duckduckgo.com",
  "mail.google.com",
  "docs.google.com",
  "calendar.google.com",
  "github.com",
  "gitlab.com",
  "stackoverflow.com",
  "claude.ai",
  "chatgpt.com",
  "chromewebstore.google.com",
  "addons.mozilla.org",
]);

function youtubeGuess(url: URL): LinkGuess {
  const params = url.searchParams;
  if (url.pathname === "/watch" && params.has("v")) {
    return params.has("list") ? "video-in-playlist" : "video";
  }
  if (url.pathname === "/playlist" && params.has("list")) return "playlist";
  if (VIDEO_PATH.test(url.pathname)) return "video";
  if (CHANNEL_PATH.test(url.pathname)) return "channel";
  if (YOUTUBE_NON_MEDIA.test(url.pathname)) return "not-media";
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
  if (NON_MEDIA_HOSTS.has(host)) return "not-media";
  return "unknown";
}

// Guesses the server is never asked about: the popup says so at once.
export function isSendable(guess: LinkGuess): boolean {
  return guess !== "unsupported" && guess !== "not-media";
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
