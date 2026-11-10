import { describe, expect, it } from "vitest";
import type { LinkJob } from "../lib/types.ts";
import { describeJob, formatBytes, isActive } from "./job-status.ts";

function job(overrides: Partial<LinkJob>): LinkJob {
  return {
    id: 1,
    status: "running",
    kind: "download",
    title: "Title",
    progress: null,
    downloaded_bytes: null,
    total_bytes: null,
    speed: null,
    eta: null,
    part: null,
    scheduled_at: null,
    error: null,
    created_at: "2026-11-10T10:00:00Z",
    finished_at: null,
    ...overrides,
  };
}

describe("describeJob", () => {
  it("shows a download's percent, speed and time left", () => {
    const view = describeJob(job({ progress: 42.5, speed: 3_100_000, eta: 75 }));
    expect(view).toEqual({
      status: "Downloading 42%",
      detail: "3.1 MB/s · 1:15 left",
      fraction: 0.425,
    });
  });

  it("shows a recording's part and size", () => {
    const view = describeJob(job({ kind: "live", part: 2, downloaded_bytes: 2_500_000_000 }));
    expect(view.status).toBe("Recording (part 2)");
    expect(view.detail).toBe("2.5 GB so far");
  });

  it("names waiting, finished and failed jobs", () => {
    expect(describeJob(job({ status: "queued" })).status).toBe("Waiting in the queue");
    expect(describeJob(job({ status: "completed" })).status).toBe("Downloaded ✓");
    expect(describeJob(job({ status: "completed", kind: "live" })).status).toBe("Recorded ✓");
    const failed = describeJob(job({ status: "failed", error: "ERROR: Video unavailable" }));
    expect(failed).toMatchObject({ status: "Last try failed", detail: "Video unavailable" });
  });
});

describe("isActive", () => {
  it("is true while a job waits or runs", () => {
    expect(isActive(job({ status: "scheduled" }))).toBe(true);
    expect(isActive(job({ status: "completed" }))).toBe(false);
    expect(isActive(null)).toBe(false);
  });
});

describe("formatBytes", () => {
  it("picks a unit", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(1_500_000)).toBe("1.5 MB");
    expect(formatBytes(250_000_000)).toBe("250 MB");
  });
});
