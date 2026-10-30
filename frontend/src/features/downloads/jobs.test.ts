import { QueryClient } from "@tanstack/react-query";

import {
  JOBS_KEY,
  applyJobEvent,
  isActiveJob,
  removeJob,
  upsertJob,
} from "@/features/downloads/jobs";
import type { Job } from "@/features/downloads/types";
import { makeJob } from "@/test/fake-jobs";

describe("job cache helpers", () => {
  const older = makeJob({ id: 1 });
  const newer = makeJob({ id: 2 });

  it("inserts new jobs newest first and replaces existing ones", () => {
    expect(upsertJob([older], newer)).toEqual([newer, older]);
    const updated = makeJob({ id: 1, status: "running" });
    expect(upsertJob([newer, older], updated)).toEqual([newer, updated]);
  });

  it("ignores updates older than the cached copy", () => {
    // Regression: a slow "running" cancel response used to overwrite "cancelled".
    const cancelled = makeJob({ id: 1, status: "cancelled", revision: 5 });
    const stale = makeJob({ id: 1, status: "running", revision: 4 });
    expect(upsertJob([cancelled], stale)).toEqual([cancelled]);
    expect(upsertJob([stale], cancelled)).toEqual([cancelled]);
  });

  it("leaves a list that hasn't loaded yet alone", () => {
    expect(upsertJob(undefined, newer)).toBeUndefined();
    expect(removeJob(undefined, 1)).toBeUndefined();
  });

  it("removes jobs", () => {
    expect(removeJob([newer, older], 2)).toEqual([older]);
  });

  it.each([
    ["queued", true],
    ["running", true],
    ["completed", false],
    ["failed", false],
    ["cancelled", false],
  ] as const)("treats %s as active: %s", (status, active) => {
    expect(isActiveJob(makeJob({ status }))).toBe(active);
  });

  it("applies WebSocket events to the cached list", () => {
    const client = new QueryClient();
    client.setQueryData<Job[]>(JOBS_KEY, [older]);
    applyJobEvent(client, { type: "job", job: newer });
    expect(client.getQueryData(JOBS_KEY)).toEqual([newer, older]);
    applyJobEvent(client, { type: "job_deleted", id: 1 });
    expect(client.getQueryData(JOBS_KEY)).toEqual([newer]);
  });
});
