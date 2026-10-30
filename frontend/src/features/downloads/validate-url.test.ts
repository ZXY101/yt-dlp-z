import { validateUrl } from "@/features/downloads/validate-url";

describe("validateUrl", () => {
  it.each([
    ["", /Paste a link/],
    ["   ", /Paste a link/],
    ["youtube.com/watch?v=x", /full link/],
    ["ftp://example.com/file", /full link/],
  ])("rejects %j", (url, message) => {
    expect(validateUrl(url)).toMatch(message);
  });

  it("accepts web links", () => {
    expect(validateUrl(" https://www.youtube.com/watch?v=abc ")).toBeUndefined();
  });
});
