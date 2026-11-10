// Drawing the popup from its state. No logic beyond showing and hiding.
import { byId, element } from "../lib/dom.ts";
import type { Problem } from "../lib/problems.ts";
import { needsSetup } from "../lib/problems.ts";
import type { MediaInfo, Preset } from "../lib/types.ts";
import { buttonLabel, describeInfo, guessLabel, presetLabel, type PopupState } from "./state.ts";

export const view = {
  setup: byId("setup"),
  openSetup: byId<HTMLButtonElement>("open-setup"),
  link: byId("link"),
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

export function showState(state: PopupState, checking: boolean): void {
  if (state.info) showInfo(state.info);
  else
    view.kind.textContent = checking
      ? `${guessLabel(state.guess)} · checking…`
      : guessLabel(state.guess);
  view.scope.hidden = state.guess !== "video-in-playlist";
  for (const button of view.scope.querySelectorAll("button")) {
    button.setAttribute(
      "aria-pressed",
      String(button.dataset.whole === String(state.wholePlaylist)),
    );
  }
  view.go.textContent = buttonLabel(state);
  view.go.disabled = state.guess === "unsupported";
}

export function showProblem(problem: Problem, text: string, onFix: (setup: boolean) => void) {
  const setup = needsSetup(problem);
  const fix = element("button", "link-button", setup ? "Open settings" : "Try again");
  fix.type = "button";
  fix.addEventListener("click", () => onFix(setup));
  view.message.className = "message error";
  view.message.replaceChildren(element("span", "", text), " ", fix);
}

export function showSent(title: string, queueUrl: string): void {
  const link = element("a", "", "Open queue");
  link.href = queueUrl;
  link.target = "_blank";
  link.rel = "noreferrer";
  view.message.className = "message ok";
  view.message.replaceChildren(element("span", "", `✓ Sent: ${title}`), " ", link);
}

export function clearMessage(): void {
  view.message.className = "message";
  view.message.replaceChildren();
}
