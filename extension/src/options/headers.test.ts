import { describe, expect, it } from "vitest";
import { formatHeaders, parseHeaders } from "./headers.ts";

describe("parseHeaders", () => {
  it("reads one header per line and skips blank lines", () => {
    const text = "CF-Access-Client-Id: abc\n\n  Authorization: Basic eDp5  \n";
    expect(parseHeaders(text)).toEqual([
      { name: "CF-Access-Client-Id", value: "abc" },
      { name: "Authorization", value: "Basic eDp5" },
    ]);
  });

  it("keeps colons in the value", () => {
    expect(parseHeaders("X-Url: http://a:b")).toEqual([{ name: "X-Url", value: "http://a:b" }]);
  });

  it("names the line that's wrong", () => {
    expect(() => parseHeaders("X-Ok: 1\nno colon here")).toThrow(/line 2/);
    expect(() => parseHeaders("bad name: 1")).toThrow(/line 1/);
  });

  it("round-trips with formatHeaders", () => {
    const headers = [{ name: "X-A", value: "1" }];
    expect(parseHeaders(formatHeaders(headers))).toEqual(headers);
  });
});
