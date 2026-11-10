import { ext } from "../lib/browser.ts";
import { failure, type Message, type Reply } from "../lib/messages.ts";
import { loadPresets } from "../lib/settings.ts";
import { startCheckingAhead } from "./check-ahead.ts";
import { showBadge } from "./feedback.ts";
import { buildMenus, handleMenuClick, hasMenus } from "./menus.ts";
import { jobs, probe, refreshPresets, send } from "./requests.ts";

async function sendFromPopup(message: Extract<Message, { type: "send" }>) {
  await showBadge(message.tabId, "busy");
  try {
    const sent = await send(message.request);
    await showBadge(message.tabId, "done");
    return sent;
  } catch (error) {
    await showBadge(message.tabId, "failed");
    throw error;
  }
}

async function refreshPresetsAndMenus(): Promise<null> {
  await buildMenus(await refreshPresets());
  return null;
}

function run(message: Message): Promise<unknown> {
  if (message.type === "probe") return probe(message.request);
  if (message.type === "send") return sendFromPopup(message);
  if (message.type === "jobs") return jobs(message.request);
  return refreshPresetsAndMenus();
}

async function answer(message: Message): Promise<Reply<unknown>> {
  try {
    return { ok: true, value: await run(message) };
  } catch (error) {
    return failure(error);
  }
}

ext.runtime.onMessage.addListener((message: Message, sender, sendResponse) => {
  // Only our own pages talk to the background script.
  if (sender.id !== ext.runtime.id) return false;
  answer(message).then(sendResponse, (error: unknown) => sendResponse(failure(error)));
  return true;
});

ext.runtime.onInstalled.addListener((details) => {
  loadPresets().then(buildMenus, console.error);
  if (details.reason === "install") ext.runtime.openOptionsPage().catch(console.error);
});

// Firefox forgets menus on restart; Chrome keeps them, and rebuilding is harmless.
ext.runtime.onStartup.addListener(() => {
  loadPresets().then(buildMenus, console.error);
});

if (hasMenus()) {
  ext.contextMenus.onClicked.addListener((info, tab) => {
    handleMenuClick(info, tab).catch(console.error);
  });
}

startCheckingAhead();
