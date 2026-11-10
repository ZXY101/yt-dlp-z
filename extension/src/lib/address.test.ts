import { describe, expect, it } from "vitest";
import { isPrivateHost, normalizeAddress, originPattern, sendsTokenInTheClear } from "./address.ts";

describe("normalizeAddress", () => {
  it("adds http:// and drops a trailing slash", () => {
    expect(normalizeAddress(" 192.168.1.5:9742/ ")).toBe("http://192.168.1.5:9742");
  });

  it("keeps https and a sub-path", () => {
    expect(normalizeAddress("https://example.org/yt/")).toBe("https://example.org/yt");
  });

  it("rejects what isn't an address", () => {
    expect(() => normalizeAddress("http://")).toThrow(/Invalid URL/);
  });
});

describe("originPattern", () => {
  it("asks for the host only, any port", () => {
    expect(originPattern("http://nas.local:9742/yt")).toBe("http://nas.local/*");
  });
});

describe("isPrivateHost", () => {
  it.each(["localhost", "nas", "10.0.0.2", "172.20.1.1", "192.168.1.5", "100.100.1.1"])(
    "%s is private",
    (host) => expect(isPrivateHost(host)).toBe(true),
  );

  it.each(["box.tail1234.ts.net", "nas.local", "[::1]", "[fd12::1]", "server.home.arpa"])(
    "%s is private",
    (host) => expect(isPrivateHost(host)).toBe(true),
  );

  it.each(["example.org", "8.8.8.8", "172.32.0.1", "100.128.0.1", "[2001:db8::1]"])(
    "%s is public",
    (host) => expect(isPrivateHost(host)).toBe(false),
  );
});

describe("sendsTokenInTheClear", () => {
  it("is true for plain HTTP to a public host", () => {
    expect(sendsTokenInTheClear("http://example.org")).toBe(true);
  });

  it("is false for HTTPS or a private host", () => {
    expect(sendsTokenInTheClear("https://example.org")).toBe(false);
    expect(sendsTokenInTheClear("http://192.168.1.5:9742")).toBe(false);
  });
});
