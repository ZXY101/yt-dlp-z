import { describeProgress, formatBytes, formatDuration } from "@/features/downloads/format";
import { makeJob } from "@/test/fake-jobs";

describe("formatBytes", () => {
  it.each([
    [0, "0 B"],
    [999, "999 B"],
    [1_500, "1.5 KB"],
    [123_456_789, "123 MB"],
    [2_500_000_000, "2.5 GB"],
    [5e15, "5000 TB"],
  ])("%d → %s", (bytes, expected) => {
    expect(formatBytes(bytes)).toBe(expected);
  });
});

describe("formatDuration", () => {
  it.each([
    [0, "0:00"],
    [45, "0:45"],
    [125, "2:05"],
    [3725, "1:02:05"],
    [-5, "0:00"],
  ])("%d → %s", (seconds, expected) => {
    expect(formatDuration(seconds)).toBe(expected);
  });
});

describe("describeProgress", () => {
  it("combines everything that is known", () => {
    const job = makeJob({
      progress: 42.7,
      downloaded_bytes: 12_300_000,
      total_bytes: 30_000_000,
      speed: 2_100_000,
      eta: 8,
    });
    expect(describeProgress(job)).toBe("42% · 12.3 MB of 30.0 MB · 2.1 MB/s · 0:08 left");
  });

  it("handles unknown totals and an empty start", () => {
    expect(describeProgress(makeJob({ downloaded_bytes: 500 }))).toBe("500 B");
    expect(describeProgress(makeJob())).toBe("Starting…");
  });
});
