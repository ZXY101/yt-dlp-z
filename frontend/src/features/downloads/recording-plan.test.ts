import { formatLiveFor, planRecording } from "@/features/downloads/recording-plan";
import { DEFAULT_RECORDING } from "@/features/presets";

const NOW = Date.parse("2026-10-31T12:00:00Z");

function hoursAgo(hours: number) {
  return new Date(NOW - hours * 3600 * 1000).toISOString();
}

describe("planRecording", () => {
  it("records upcoming and recent streams from the start", () => {
    const expected = { fromStart: true, partHours: 6, maxHours: null };
    expect(planRecording(DEFAULT_RECORDING, null, NOW)).toEqual(expected);
    expect(planRecording(DEFAULT_RECORDING, hoursAgo(1), NOW)).toEqual(expected);
  });

  it("records long-running streams from now", () => {
    expect(planRecording(DEFAULT_RECORDING, hoursAgo(10), NOW).fromStart).toBe(false);
  });

  it("can record the first hours of long-running streams instead", () => {
    const recording = { ...DEFAULT_RECORDING, long_streams: "first_hours" as const };
    expect(planRecording(recording, hoursAgo(10), NOW)).toEqual({
      fromStart: true,
      partHours: 6,
      maxHours: 6,
    });
    const shorter = { ...recording, max_hours: 2 };
    expect(planRecording(shorter, hoursAgo(10), NOW).maxHours).toBe(2);
  });

  it("always records from the start without a limit", () => {
    const recording = { ...DEFAULT_RECORDING, from_start_max_hours: null };
    expect(planRecording(recording, hoursAgo(100), NOW).fromStart).toBe(true);
  });
});

it("formats how long a stream has been live", () => {
  expect(formatLiveFor(10)).toBe("1 min");
  expect(formatLiveFor(40 * 60)).toBe("40 min");
  expect(formatLiveFor(3 * 3600 + 20 * 60)).toBe("3 h 20 min");
});
