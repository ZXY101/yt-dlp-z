// Right-click menu: send a link or the page with the default preset, or with a chosen one.
import { ext } from "../lib/browser.ts";
import { guessLink, isWholeList } from "../lib/link-guess.ts";
import { asServerProblem } from "../lib/problems.ts";
import type { Preset } from "../lib/types.ts";
import { notify, showBadge } from "./feedback.ts";
import { send } from "./requests.ts";

const SEND = "send";
const SEND_WITH = "send-with";
const WHOLE_PLAYLIST = "send-whole-playlist";
const PRESET_PREFIX = "preset:";

type Context = "link" | "page" | "video" | "audio";
const EVERYWHERE: [Context, ...Context[]] = ["link", "page", "video", "audio"];
// Videos opened from a playlist (watch?v=…&list=…); match patterns include the query.
const IN_PLAYLIST = ["*://*/watch?*list=*", "*://youtu.be/*list=*"];

function create(properties: chrome.contextMenus.CreateProperties): void {
  ext.contextMenus.create(properties, () => {
    // Read the error so a duplicate id during a quick rebuild isn't reported as unchecked.
    void ext.runtime.lastError;
  });
}

function createWholePlaylistItems(): void {
  const title = "Send whole playlist to yt-dlp-z";
  create({
    id: `${WHOLE_PLAYLIST}:link`,
    title,
    contexts: ["link"],
    targetUrlPatterns: IN_PLAYLIST,
  });
  create({
    id: `${WHOLE_PLAYLIST}:page`,
    title,
    contexts: ["page"],
    documentUrlPatterns: IN_PLAYLIST,
  });
}

// Firefox for Android has no context menus at all; the popup still works there.
export function hasMenus(): boolean {
  return (ext as Partial<typeof chrome>).contextMenus !== undefined;
}

export async function buildMenus(presets: Preset[]): Promise<void> {
  if (!hasMenus()) return;
  await ext.contextMenus.removeAll();
  create({ id: SEND, title: "Send to yt-dlp-z", contexts: EVERYWHERE });
  createWholePlaylistItems();
  if (presets.length === 0) return;
  create({ id: SEND_WITH, title: "Send to yt-dlp-z with", contexts: EVERYWHERE });
  for (const preset of presets) {
    const id = `${PRESET_PREFIX}${preset.id}`;
    create({ id, parentId: SEND_WITH, title: preset.name, contexts: EVERYWHERE });
  }
}

function presetIdOf(menuItemId: string): number | null {
  if (!menuItemId.startsWith(PRESET_PREFIX)) return null;
  return Number(menuItemId.slice(PRESET_PREFIX.length));
}

// The server's refusal names an API field; point to the popup instead.
function forMenu(message: string): string {
  return message.replace(/Set whole_playlist to download them all\.?/, "Use the toolbar button.");
}

function clickedUrl(info: chrome.contextMenus.OnClickData, tab?: chrome.tabs.Tab) {
  return info.linkUrl ?? info.pageUrl ?? tab?.url;
}

export async function handleMenuClick(
  info: chrome.contextMenus.OnClickData,
  tab?: chrome.tabs.Tab,
): Promise<void> {
  const url = clickedUrl(info, tab);
  if (!url) return;
  const menuItemId = String(info.menuItemId);
  const wholePlaylist = menuItemId.startsWith(WHOLE_PLAYLIST);
  if (!wholePlaylist && isWholeList(guessLink(url))) {
    await notify("Use the toolbar button", "Whole playlists and channels are sent from there.");
    return;
  }
  const tabId = tab?.id ?? null;
  await showBadge(tabId, "busy");
  try {
    const sent = await send({ url, presetId: presetIdOf(menuItemId), wholePlaylist });
    await showBadge(tabId, "done");
    await notify("Sent to yt-dlp-z", sent.job.title ?? url);
  } catch (error) {
    await showBadge(tabId, "failed");
    await notify("Couldn't send to yt-dlp-z", forMenu(asServerProblem(error).message));
  }
}
