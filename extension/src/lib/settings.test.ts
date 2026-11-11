import { describe, expect, it, vi } from "vitest";

const getAll = vi.fn<() => Promise<unknown>>();
vi.mock("./browser.ts", () => ({ ext: { permissions: { getAll } } }));

const { checkAheadPermissions, checkAheadRequest, hasDataConsent } = await import("./settings.ts");

describe("check links ahead permissions", () => {
  it("asks for tabs only where the browser has no data consent", () => {
    expect(checkAheadPermissions(false)).toEqual({ permissions: ["tabs"] });
  });

  it("also asks to send browsing activity where it has", () => {
    expect(checkAheadPermissions(true)).toEqual({
      permissions: ["tabs"],
      data_collection: ["browsingActivity"],
    });
  });

  it("sees data consent from getAll()'s data_collection list, even an empty one", () => {
    expect(hasDataConsent({ permissions: [], data_collection: [] })).toBe(true);
    expect(hasDataConsent({ permissions: ["tabs"] })).toBe(false);
  });

  it("builds the request from what the browser reports", async () => {
    getAll.mockResolvedValueOnce({ permissions: [], origins: [], data_collection: ["none"] });
    await expect(checkAheadRequest()).resolves.toEqual(checkAheadPermissions(true));
    getAll.mockResolvedValueOnce({ permissions: [], origins: [] });
    await expect(checkAheadRequest()).resolves.toEqual(checkAheadPermissions(false));
  });
});
