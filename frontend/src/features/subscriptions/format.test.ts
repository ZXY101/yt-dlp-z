import { describeCheck, formatRelative } from "@/features/subscriptions/format";
import { makeSubscription } from "@/test/fake-subscriptions";

const NOW = Date.parse("2026-10-30T12:00:00Z");

describe("formatRelative", () => {
  it.each([
    ["2026-10-30T11:59:30Z", "just now"],
    ["2026-10-30T11:55:00Z", "5 minutes ago"],
    ["2026-10-30T09:00:00Z", "3 hours ago"],
    ["2026-10-29T12:00:00Z", "yesterday"],
    ["2026-11-02T12:00:00Z", "in 3 days"],
    ["2026-12-30T12:00:00Z", "in 2 months"],
    ["2024-10-30T12:00:00Z", "2 years ago"],
  ])("formats %s as %s", (iso, expected) => {
    expect(formatRelative(iso, NOW)).toBe(expected);
  });
});

describe("describeCheck", () => {
  it("describes each check state", () => {
    expect(describeCheck(makeSubscription({ checking: true }), NOW)).toBe("Checking now…");
    expect(describeCheck(makeSubscription(), NOW)).toBe("Not checked yet");
    const checked = makeSubscription({ last_checked_at: "2026-10-30T11:50:00Z" });
    expect(describeCheck(checked, NOW)).toBe("Checked 10 minutes ago");
  });
});
