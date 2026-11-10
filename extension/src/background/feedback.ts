// How a send shows up outside the popup: the toolbar badge and, for menu sends, a notification.
import { ext } from "../lib/browser.ts";

const CLEAR_AFTER_MS = 5000;
const COLORS = { busy: "#6b7280", done: "#16a34a", failed: "#dc2626" };

type BadgeState = keyof typeof COLORS;
const TEXT: Record<BadgeState, string> = { busy: "…", done: "✓", failed: "✗" };

async function setBadge(target: { tabId?: number }, state: BadgeState): Promise<void> {
  await ext.action.setBadgeBackgroundColor({ ...target, color: COLORS[state] });
  await ext.action.setBadgeText({ ...target, text: TEXT[state] });
}

// Never throws: a closed tab must not turn a working send into an error.
export async function showBadge(tabId: number | null, state: BadgeState): Promise<void> {
  const target = tabId === null ? {} : { tabId };
  try {
    await setBadge(target, state);
  } catch {
    return;
  }
  if (state === "busy") return;
  setTimeout(() => {
    ext.action.setBadgeText({ ...target, text: "" }).catch(() => {
      // The tab may be closed by now.
    });
  }, CLEAR_AFTER_MS);
}

export async function notify(title: string, message: string): Promise<void> {
  await ext.notifications.create({
    type: "basic",
    iconUrl: ext.runtime.getURL("icons/icon-128.png"),
    title,
    message,
  });
}
