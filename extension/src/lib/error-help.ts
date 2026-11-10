import type { Problem } from "./problems.ts";

// Turning yt-dlp's errors into a short headline and a tip, keeping the full text for the
// "Details" toggle. yt-dlp's messages are long, technical and often hold the whole link.

export interface ErrorHelp {
  title: string;
  tip: string | null;
  // The original text, when the headline doesn't already say everything.
  details: string | null;
}

interface KnownError {
  match: RegExp;
  title: string;
  tip: string;
}

// Checked in order: the first match wins.
const KNOWN_ERRORS: KnownError[] = [
  {
    match: /unsupported url/i,
    title: "yt-dlp doesn't support this page",
    tip: "Open the video's own page, or use a direct link to the video.",
  },
  {
    match:
      /connection refused|failed to establish a new connection|name or service not known|nodename nor servname|getaddrinfo failed|temporary failure in name resolution/i,
    title: "Your server couldn't open this page",
    tip: "The yt-dlp-z server fetches the page itself, so the address has to work from the server, not just from this browser. localhost or the server's own name point at the server itself.",
  },
  {
    match: /timed out|read timeout/i,
    title: "The site took too long to answer",
    tip: "Try again in a moment. If it keeps happening, check the server's internet connection or proxy.",
  },
  {
    match: /not a bot|confirm you.re not a bot/i,
    title: "YouTube asked for a bot check",
    tip: "Set up PO tokens in yt-dlp-z (Settings → PO tokens), or pick a preset with cookies.",
  },
  {
    match: /members?-only|join this channel/i,
    title: "Members-only video",
    tip: "Pick a preset with cookies from an account that is a member of the channel.",
  },
  {
    match: /sign in to confirm your age|age[- ]restricted|inappropriate for some users/i,
    title: "Age-restricted video",
    tip: "Pick a preset with cookies from a signed-in account.",
  },
  {
    match: /private video|video is private/i,
    title: "This video is private",
    tip: "Only accounts the uploader shared it with can see it: pick a preset with that account's cookies.",
  },
  {
    match: /not available in your country|geo.?restrict|blocked it in your country/i,
    title: "Not available in the server's country",
    tip: "Use a proxy in another country (Settings → Proxies).",
  },
  {
    match:
      /video unavailable|video is unavailable|has been removed|no longer available|account .* terminated/i,
    title: "Video unavailable",
    tip: "It may have been deleted or made unlisted. Check the page still plays in the browser.",
  },
  {
    match: /http error 429|too many requests/i,
    title: "The site is limiting requests",
    tip: "Wait a while before trying again, or spread downloads over proxies (Settings → Proxies).",
  },
  {
    match: /http error 403|forbidden/i,
    title: "The site refused the download",
    tip: "Update yt-dlp (Settings → yt-dlp): sites change often and older versions get refused.",
  },
  {
    match: /requested format is not available/i,
    title: "That quality isn't available",
    tip: "Pick another preset, or one with a less strict quality.",
  },
];

// "ERROR: [youtube] abc123: Video unavailable" → "Video unavailable"
function plainText(message: string): string {
  return message
    .replace(/^(ERROR|WARNING):\s*/i, "")
    .replace(/^\[[\w:-]+\]\s*(?:[\w-]+:\s*)?/, "")
    .trim();
}

const MAX_TITLE_LENGTH = 120;

function headline(text: string): string {
  const firstSentence = text.split(/(?<=[.!?])\s|\n/)[0] ?? text;
  if (firstSentence.length <= MAX_TITLE_LENGTH) return firstSentence;
  return `${firstSentence.slice(0, MAX_TITLE_LENGTH).trimEnd()}…`;
}

export function explainError(message: string): ErrorHelp {
  const text = plainText(message);
  const known = KNOWN_ERRORS.find((entry) => entry.match.test(text));
  if (known) return { title: known.title, tip: known.tip, details: message.trim() };
  const title = headline(text);
  return { title, tip: null, details: title === message.trim() ? null : message.trim() };
}

const UNREACHABLE_TIP =
  "Check that the server is running and that this device can reach it (same network, VPN or Tailscale).";
const HTTPS_ONLY_TIP =
  "Firefox's HTTPS-Only Mode turns http:// into https:// for server names. Use the server's IP address or its HTTPS address, or add an exception.";

/** Help for a failed request: yt-dlp's errors are explained, the extension's own are short. */
export function helpFor(problem: Problem, message: string): ErrorHelp {
  if (problem === "rejected" || problem === "server-error") return explainError(message);
  if (problem === "unreachable") {
    const tip = message.includes("HTTPS-Only") ? HTTPS_ONLY_TIP : UNREACHABLE_TIP;
    return { title: "Can't reach your yt-dlp-z server", tip, details: message };
  }
  return { title: message, tip: null, details: null };
}
