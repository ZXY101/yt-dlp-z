import { ext } from "../lib/browser.ts";
import { isSendable } from "../lib/link-guess.ts";
import { guessPage } from "../lib/page-guess.ts";
import { askProbe, askRefreshPresets, askSend } from "../lib/messages.ts";
import {
  loadConnection,
  loadLastPresetId,
  loadPresets,
  saveLastPresetId,
} from "../lib/settings.ts";
import type { LinkJob, Preset, SentLink } from "../lib/types.ts";
import { refreshJobs } from "./jobs.ts";
import { currentJob, probeRequestFor, sendRequestFor, type PopupState } from "./state.ts";
import {
  clearMessage,
  showJob,
  showNote,
  showPresets,
  showProblem,
  showQueueLink,
  showSending,
  showState,
  showTab,
  view,
} from "./view.ts";

let state: PopupState;
let tabId: number | null = null;
let checking = false;
let sending = false;
// The server's check said this link can't be downloaded (unavailable, unsupported…): sending
// would fail the same way, so Download waits for a check that passes.
let checkRejected = false;
// Each check gets a number, so a slow answer to an older question is ignored.
let latestCheck = 0;

function render(): void {
  showState(state, checking);
  showJob(currentJob(state));
  if (sending) showSending();
  else if (checkRejected) view.go.disabled = true;
}

function handleJobs(jobs: LinkJob[]): void {
  state.jobs = jobs;
  render();
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
  if (!isSendable(state.guess)) return;
  const check = ++latestCheck;
  checking = true;
  checkRejected = false;
  state.info = null;
  render();
  refreshJobs(state, handleJobs).catch(console.error);
  const reply = await askProbe(probeRequestFor(state));
  if (check !== latestCheck) return;
  checking = false;
  if (reply.ok) state.info = reply.value;
  else {
    checkRejected = reply.problem === "rejected";
    showProblem(reply.problem, reply.message, handleFix);
  }
  render();
}

function sentNote(sent: SentLink): string {
  if (!sent.existing) return `✓ Sent: ${sent.job.title ?? state.url}`;
  if (sent.job.status === "completed") {
    return "Already downloaded with this preset. Pick another one for a different copy.";
  }
  return "Already in the queue with these settings.";
}

async function handleGo(): Promise<void> {
  clearMessage();
  sending = true;
  render();
  const reply = await askSend(sendRequestFor(state), tabId);
  sending = false;
  if (!reply.ok) {
    render();
    showProblem(reply.problem, reply.message, handleFix);
    return;
  }
  state.jobs = [reply.value.job, ...state.jobs.filter((job) => job.id !== reply.value.job.id)];
  state.anotherCopy = false;
  render();
  showNote(sentNote(reply.value));
  refreshJobs(state, handleJobs).catch(console.error);
}

function handlePresetChange(): void {
  const cookieBefore = probeRequestFor(state).cookieId;
  state.presetId = view.preset.value ? Number(view.preset.value) : null;
  saveLastPresetId(state.presetId).catch(console.error);
  // Cookies change what the server can see (members-only videos), so check again.
  if (probeRequestFor(state).cookieId !== cookieBefore) runCheck().catch(console.error);
}

function handleAnotherCopy(): void {
  state.anotherCopy = true;
  clearMessage();
  render();
  view.preset.focus();
}

function handleScopeClick(event: MouseEvent): void {
  const button = (event.target as HTMLElement).closest("button");
  if (!button) return;
  state.wholePlaylist = button.dataset.whole === "true";
  state.jobs = [];
  state.anotherCopy = false;
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

async function initialState(tab: chrome.tabs.Tab | undefined, serverAddress: string) {
  const url = tab?.url ?? "";
  const [presets, presetId] = await Promise.all([loadPresets(), loadLastPresetId()]);
  const known = presets.some((preset) => preset.id === presetId);
  const guess = guessPage(url, { serverAddress, title: tab?.title });
  const base = { url, guess, info: null, wholePlaylist: false, jobs: [], anotherCopy: false };
  const initial: PopupState = { ...base, presets, presetId: known ? presetId : null };
  return initial;
}

function listen(): void {
  view.go.addEventListener("click", () => handleGo().catch(console.error));
  view.preset.addEventListener("change", handlePresetChange);
  view.scope.addEventListener("click", handleScopeClick);
  view.another.addEventListener("click", handleAnotherCopy);
  followPresetChanges();
}

async function start(): Promise<void> {
  const connection = await loadConnection();
  if (!connection) {
    showSetup();
    return;
  }
  showQueueLink(connection.address);
  const tab = await activePageTab();
  state = await initialState(tab, connection.address);
  tabId = tab?.id ?? null;
  view.link.hidden = false;
  if (tab) showTab(tab);
  showPresets(state.presets, state.presetId);
  listen();
  render();
  runCheck().catch(console.error);
  askRefreshPresets().catch(console.error);
}

start().catch(console.error);
