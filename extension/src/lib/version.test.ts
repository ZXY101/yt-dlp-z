import { describe, expect, it } from "vitest";
import { isAtLeast } from "./version.ts";

describe("isAtLeast", () => {
  it.each([
    ["0.1.6", "0.1.6", true],
    ["0.1.10", "0.1.6", true],
    ["0.2.0", "0.1.6", true],
    ["v1.0.0", "0.1.6", true],
    ["0.1.5", "0.1.6", false],
    ["0.0.9", "0.1.6", false],
    ["0.1.7.dev3+gabc", "0.1.6", true],
  ])("%s ≥ %s is %s", (version, minimum, expected) => {
    expect(isAtLeast(version, minimum)).toBe(expected);
  });
});
