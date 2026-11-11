// "Check links ahead": after a few seconds on a video page, ask the server to check it, so the
// popup answers from the server's cache at once. Opt-in, and needs the optional "tabs"
// permission to see tab addresses plus, on Firefox, consent to send browsing activity.
import { ext } from "../lib/browser.ts";
import { guessLink, isVideoPage } from "../lib/link-guess.ts";
import type { ProbeRequest } from "../lib/server.ts";
import {
  checkAheadRequest,
  loadCheckAhead,
  loadLastPresetId,
  loadPresets,
} from "../lib/settings.ts";
import { probe } from "./requests.ts";

const DELAY_MS = 3000;

let timer: ReturnType<typeof setTimeout> | undefined;
let running = false;

async function isEnabled(): Promise<boolean> {
  return (await loadCheckAhead()) && (await ext.permissions.contains(await checkAheadRequest()));
}

// The same request the popup makes when it opens, so it finds this check in the cache.
async function popupRequest(url: string): Promise<ProbeRequest> {
  const [presets, presetId] = await Promise.all([loadPresets(), loadLastPresetId()]);
  const preset = presets.find((candidate) => candidate.id === presetId);
  const noPlaylist = guessLink(url) === "video-in-playlist";
  return { url, cookieId: preset?.cookie_id ?? null, noPlaylist };
}

async function checkIfStillOpen(tabId: number, url: string): Promise<void> {
  const [tab] = await ext.tabs.query({ active: true, lastFocusedWindow: true });
  // One check at a time; a page left within the delay is dropped.
  if (running || tab?.id !== tabId || tab.url !== url) return;
  running = true;
  try {
    await probe(await popupRequest(url));
  } catch {
    // The popup shows the problem if the user opens it.
  } finally {
    running = false;
  }
}

async function watchPage(tab: chrome.tabs.Tab): Promise<void> {
  clearTimeout(timer);
  const { id, url } = tab;
  if (id === undefined || !url || !isVideoPage(url) || !(await isEnabled())) return;
  timer = setTimeout(() => {
    checkIfStillOpen(id, url).catch(console.error);
  }, DELAY_MS);
}

export function startCheckingAhead(): void {
  ext.tabs.onActivated.addListener(({ tabId }) => {
    ext.tabs.get(tabId).then(watchPage, console.error);
  });
  // Fires for in-page navigation too (pushState on single-page sites).
  ext.tabs.onUpdated.addListener((_tabId, change, tab) => {
    if (change.url && tab.active) watchPage(tab).catch(console.error);
  });
}
