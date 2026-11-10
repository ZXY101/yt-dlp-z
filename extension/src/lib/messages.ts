// Messages from the popup and options page to the background script, which makes every
// request, so closing the popup mid-request loses nothing.
import { ext } from "./browser.ts";
import { asServerProblem, type Problem } from "./problems.ts";
import type { ProbeRequest, SendRequest } from "./server.ts";
import type { MediaInfo, SentLink } from "./types.ts";

export type Message =
  | { type: "probe"; request: ProbeRequest }
  | { type: "send"; request: SendRequest; tabId: number | null }
  | { type: "refresh-presets" };

export type Reply<T> = { ok: true; value: T } | { ok: false; problem: Problem; message: string };

export function failure(error: unknown): Reply<never> {
  const problem = asServerProblem(error);
  return { ok: false, problem: problem.problem, message: problem.message };
}

function ask<T>(message: Message): Promise<Reply<T>> {
  return ext.runtime.sendMessage(message);
}

export function askProbe(request: ProbeRequest): Promise<Reply<MediaInfo>> {
  return ask({ type: "probe", request });
}

export function askSend(request: SendRequest, tabId: number | null): Promise<Reply<SentLink>> {
  return ask({ type: "send", request, tabId });
}

// Fetches the presets again and caches them; listen to storage changes for the result.
export function askRefreshPresets(): Promise<Reply<null>> {
  return ask({ type: "refresh-presets" });
}
