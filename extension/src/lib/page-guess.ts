// The link guess, plus what only this extension knows: which address is the user's own
// yt-dlp-z server. Its dashboard has nothing to download, and asking the server to fetch its
// own page fails with a confusing connection error.
import { guessLink, type LinkGuess } from "./link-guess.ts";

// What the dashboard calls itself in the tab, on any yt-dlp-z server.
const DASHBOARD_TITLE = "yt-dlp-z";
const LOOPBACK = /^(localhost|127(\.\d{1,3}){3}|\[::1\])$/i;

interface PageContext {
  serverAddress: string | null;
  title?: string;
}

function hostOf(address: string): string | null {
  try {
    return new URL(address).host.toLowerCase();
  } catch {
    return null;
  }
}

function isOwnServer(address: string, context: PageContext): boolean {
  if (context.title === DASHBOARD_TITLE) return true;
  if (!context.serverAddress) return false;
  const host = hostOf(address);
  return host !== null && host === hostOf(context.serverAddress);
}

function isThisComputer(address: string): boolean {
  try {
    return LOOPBACK.test(new URL(address).hostname);
  } catch {
    return false;
  }
}

export function guessPage(address: string, context: PageContext): LinkGuess {
  const guess = guessLink(address);
  if (guess === "unsupported") return guess;
  if (isOwnServer(address, context)) return "own-server";
  if (isThisComputer(address)) return "this-computer";
  return guess;
}
