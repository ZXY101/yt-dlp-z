// Keeps the popup's view of the link's jobs fresh while a download or recording runs.
import { askJobs } from "../lib/messages.ts";
import type { LinkJob } from "../lib/types.ts";
import { isActive } from "./job-status.ts";
import { jobsRequestFor, type PopupState } from "./state.ts";

const POLL_MS = 1500;

let timer: ReturnType<typeof setTimeout> | undefined;
// Each refresh gets a number, so an answer for an older question is dropped.
let latest = 0;

export async function refreshJobs(state: PopupState, onJobs: (jobs: LinkJob[]) => void) {
  clearTimeout(timer);
  const refresh = ++latest;
  const reply = await askJobs(jobsRequestFor(state));
  // No jobs view on errors: the link check already shows what's wrong.
  if (refresh !== latest || !reply.ok) return;
  onJobs(reply.value);
  if (isActive(reply.value[0] ?? null)) {
    timer = setTimeout(() => {
      refreshJobs(state, onJobs).catch(console.error);
    }, POLL_MS);
  }
}
