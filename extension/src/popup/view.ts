// Drawing the popup from its state. No logic beyond showing and hiding.
import { byId, element } from "../lib/dom.ts";
import type { Problem } from "../lib/problems.ts";
import { needsSetup } from "../lib/problems.ts";
import { isSendable } from "../lib/link-guess.ts";
import type { LinkJob, MediaInfo, Preset } from "../lib/types.ts";
import { helpFor, type ErrorHelp } from "../lib/error-help.ts";
import { describeJob } from "./job-status.ts";
import {
  actionMode,
  buttonLabel,
  describeInfo,
  guessLabel,
  presetLabel,
  type PopupState,
} from "./state.ts";

export const view = {
  setup: byId("setup"),
  openSetup: byId<HTMLButtonElement>("open-setup"),
  link: byId("link"),
  queueLink: byId<HTMLAnchorElement>("queue-link"),
  job: byId("job"),
  jobStatus: byId("job-status"),
  jobBar: byId<HTMLProgressElement>("job-bar"),
  jobDetail: byId("job-detail"),
  choices: byId("choices"),
  presetField: byId("preset-field"),
  another: byId<HTMLButtonElement>("another"),
  favicon: byId<HTMLImageElement>("favicon"),
  title: byId("title"),
  kind: byId("kind"),
  thumbnail: byId<HTMLImageElement>("thumbnail"),
  scope: byId("scope"),
  preset: byId<HTMLSelectElement>("preset"),
  go: byId<HTMLButtonElement>("go"),
  message: byId("message"),
};

export function showTab(tab: chrome.tabs.Tab): void {
  view.title.textContent = tab.title || tab.url || "";
  if (tab.favIconUrl?.startsWith("http")) {
    view.favicon.src = tab.favIconUrl;
    view.favicon.hidden = false;
  }
}

export function showPresets(presets: Preset[], selected: number | null): void {
  const options = [new Option("Default for this kind of link", "")];
  for (const preset of presets) options.push(new Option(presetLabel(preset), String(preset.id)));
  view.preset.replaceChildren(...options);
  const known = presets.some((preset) => preset.id === selected);
  view.preset.value = known ? String(selected) : "";
}

function showInfo(info: MediaInfo): void {
  view.kind.textContent = describeInfo(info);
  if (info.title) view.title.textContent = info.title;
  if (info.thumbnail) {
    view.thumbnail.src = info.thumbnail;
    view.thumbnail.hidden = false;
  }
}

export function showQueueLink(address: string): void {
  view.queueLink.href = `${address}/queue`;
  view.queueLink.hidden = false;
}

export function showJob(job: LinkJob | null): void {
  view.job.hidden = job === null;
  if (!job) return;
  const { status, detail, fraction } = describeJob(job);
  view.jobStatus.textContent = status;
  view.jobDetail.textContent = detail;
  view.jobBar.hidden = fraction === null;
  // A progress element without a value shows as busy.
  if (fraction === undefined || fraction === null) view.jobBar.removeAttribute("value");
  else view.jobBar.value = fraction;
}

function kindText(state: PopupState, checking: boolean): string {
  const label = guessLabel(state.guess);
  return checking ? `${label} · checking…` : label;
}

export function showState(state: PopupState, checking: boolean): void {
  if (state.info) showInfo(state.info);
  else view.kind.textContent = kindText(state, checking);
  view.choices.hidden = !isSendable(state.guess);
  view.scope.hidden = state.guess !== "video-in-playlist";
  for (const button of view.scope.querySelectorAll("button")) {
    button.setAttribute(
      "aria-pressed",
      String(button.dataset.whole === String(state.wholePlaylist)),
    );
  }
  showAction(state);
}

function showAction(state: PopupState): void {
  const mode = actionMode(state);
  view.presetField.hidden = mode !== "send";
  view.go.hidden = mode === "done";
  view.another.hidden = mode !== "done";
  view.go.classList.toggle("busy", mode === "busy");
  view.go.disabled = mode === "busy";
  view.go.textContent = buttonLabel(state);
}

export function showSending(): void {
  view.go.classList.add("busy");
  view.go.disabled = true;
  view.go.textContent = "Sending…";
}

function detailsToggle(details: string): HTMLDetailsElement {
  const toggle = element("details", "error-details");
  toggle.append(element("summary", "", "Details"), element("pre", "", details));
  return toggle;
}

function errorBox(help: ErrorHelp): HTMLElement[] {
  const parts: HTMLElement[] = [element("div", "error-title", help.title)];
  if (help.tip) parts.push(element("div", "error-tip", help.tip));
  if (help.details) parts.push(detailsToggle(help.details));
  return parts;
}

export function showProblem(problem: Problem, text: string, onFix: (setup: boolean) => void) {
  const setup = needsSetup(problem);
  const fix = element("button", "link-button", setup ? "Open settings" : "Try again");
  fix.type = "button";
  fix.addEventListener("click", () => onFix(setup));
  view.message.className = "message error-box";
  view.message.replaceChildren(...errorBox(helpFor(problem, text)), fix);
}

export function showNote(text: string): void {
  view.message.className = "message ok";
  view.message.replaceChildren(element("span", "", text));
}

export function clearMessage(): void {
  view.message.className = "message";
  view.message.replaceChildren();
}
