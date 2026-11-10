import { ext } from "../lib/browser.ts";
import { guessLink } from "../lib/link-guess.ts";
import { askProbe, askRefreshPresets, askSend } from "../lib/messages.ts";
import {
  loadConnection,
  loadLastPresetId,
  loadPresets,
  saveLastPresetId,
  type Connection,
} from "../lib/settings.ts";
import type { Preset } from "../lib/types.ts";
import { probeRequestFor, sendRequestFor, type PopupState } from "./state.ts";
import {
  clearMessage,
  showPresets,
  showProblem,
  showSent,
  showState,
  showTab,
  view,
} from "./view.ts";

const CLOSE_AFTER_MS = 2000;

let state: PopupState;
let tabId: number | null = null;
let checking = false;
let sent = false;
// Each check gets a number, so a slow answer to an older question is ignored.
let latestCheck = 0;

function render(): void {
  showState(state, checking);
  if (sent) view.go.disabled = true;
}

function handleFix(setup: boolean): void {
  if (setup) {
    ext.runtime.openOptionsPage().catch(console.error);
    return;
  }
  clearMessage();
  runCheck().catch(console.error);
}

async function runCheck(): Promise<void> {
  if (state.guess === "unsupported") return;
  const check = ++latestCheck;
  checking = true;
  state.info = null;
  render();
  const reply = await askProbe(probeRequestFor(state));
  if (check !== latestCheck) return;
  checking = false;
  if (reply.ok) state.info = reply.value;
  else showProblem(reply.problem, reply.message, handleFix);
  render();
}

function closeSoon(): void {
  let timer = setTimeout(() => window.close(), CLOSE_AFTER_MS);
  document.body.addEventListener("mouseenter", () => clearTimeout(timer));
  document.body.addEventListener("mouseleave", () => {
    timer = setTimeout(() => window.close(), CLOSE_AFTER_MS);
  });
}

async function handleGo(connection: Connection): Promise<void> {
  clearMessage();
  view.go.disabled = true;
  view.go.textContent = "Sending…";
  const reply = await askSend(sendRequestFor(state), tabId);
  render();
  if (!reply.ok) {
    showProblem(reply.problem, reply.message, handleFix);
    return;
  }
  const title = reply.value.job.title ?? state.info?.title ?? state.url;
  sent = true;
  render();
  showSent(title, `${connection.address}/queue`);
  closeSoon();
}

function handlePresetChange(): void {
  const cookieBefore = probeRequestFor(state).cookieId;
  state.presetId = view.preset.value ? Number(view.preset.value) : null;
  saveLastPresetId(state.presetId).catch(console.error);
  // Cookies change what the server can see (members-only videos), so check again.
  if (probeRequestFor(state).cookieId !== cookieBefore) runCheck().catch(console.error);
}

function handleScopeClick(event: MouseEvent): void {
  const button = (event.target as HTMLElement).closest("button");
  if (!button) return;
  state.wholePlaylist = button.dataset.whole === "true";
  runCheck().catch(console.error);
}

function followPresetChanges(): void {
  ext.storage.onChanged.addListener((changes, area) => {
    const presets = changes.presets?.newValue as Preset[] | undefined;
    if (area !== "local" || !presets) return;
    state.presets = presets;
    showPresets(presets, state.presetId);
  });
}

function showSetup(): void {
  view.setup.hidden = false;
  view.openSetup.addEventListener("click", () => {
    ext.runtime.openOptionsPage().then(() => window.close(), console.error);
  });
}

// Firefox for Android may show the popup as a tab of its own: then look past it.
async function activePageTab(): Promise<chrome.tabs.Tab | undefined> {
  const own = ext.runtime.getURL("");
  const [tab] = await ext.tabs.query({ active: true, currentWindow: true });
  if (!tab?.url?.startsWith(own)) return tab;
  const candidates = await ext.tabs.query({ active: true });
  return candidates.find((candidate) => !candidate.url?.startsWith(own));
}

async function start(): Promise<void> {
  const connection = await loadConnection();
  if (!connection) {
    showSetup();
    return;
  }
  const tab = await activePageTab();
  const url = tab?.url ?? "";
  const [presets, presetId] = await Promise.all([loadPresets(), loadLastPresetId()]);
  const known = presets.some((preset) => preset.id === presetId);
  state = {
    url,
    guess: guessLink(url),
    info: null,
    wholePlaylist: false,
    presets,
    presetId: known ? presetId : null,
  };
  tabId = tab?.id ?? null;
  view.link.hidden = false;
  if (tab) showTab(tab);
  showPresets(presets, state.presetId);
  view.go.addEventListener("click", () => handleGo(connection).catch(console.error));
  view.preset.addEventListener("change", handlePresetChange);
  view.scope.addEventListener("click", handleScopeClick);
  followPresetChanges();
  runCheck().catch(console.error);
  askRefreshPresets().catch(console.error);
}

start().catch(console.error);
