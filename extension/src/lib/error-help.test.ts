import { describe, expect, it } from "vitest";
import { explainError, helpFor } from "./error-help.ts";

describe("explainError", () => {
  it("explains a page the server can't reach, keeping the original as details", () => {
    const message =
      "Unable to download webpage: HTTPConnection(host='zxy-server', port=9743): Failed to " +
      "establish a new connection: [Errno 111] Connection refused";
    const help = explainError(message);
    expect(help.title).toBe("Your server couldn't open this page");
    expect(help.tip).toMatch(/has to work from the server/);
    expect(help.details).toBe(message);
  });

  it.each([
    ["ERROR: Unsupported URL: https://example.org/x", "yt-dlp doesn't support this page"],
    ["ERROR: [youtube] abc: Sign in to confirm you're not a bot.", "YouTube asked for a bot check"],
    ["Join this channel to get access to members-only content", "Members-only video"],
    ["ERROR: [youtube] abc: Video unavailable", "Video unavailable"],
    [
      "ERROR: [youtube] abc: Private video. Sign in if you've been granted access",
      "This video is private",
    ],
    ["HTTP Error 429: Too Many Requests", "The site is limiting requests"],
    [
      "ERROR: unable to download video data: HTTP Error 403: Forbidden",
      "The site refused the download",
    ],
  ])("knows %s", (message, title) => {
    expect(explainError(message).title).toBe(title);
  });

  it("shortens an unknown error to its first sentence", () => {
    const help = explainError("ERROR: [site] 12: Something odd happened. More text follows here.");
    expect(help).toEqual({
      title: "Something odd happened.",
      tip: null,
      details: "ERROR: [site] 12: Something odd happened. More text follows here.",
    });
  });

  it("has no details when the headline is the whole message", () => {
    expect(explainError("The server took too long to answer.").details).toBeNull();
  });
});

describe("helpFor", () => {
  it("explains yt-dlp's errors the server passes on", () => {
    expect(helpFor("rejected", "ERROR: [youtube] a: Video unavailable").title).toBe(
      "Video unavailable",
    );
  });

  it("gives the extension's own problems a short headline", () => {
    const help = helpFor("unreachable", "Can't reach http://nas:9742 (NetworkError).");
    expect(help.title).toBe("Can't reach your yt-dlp-z server");
    expect(help.details).toBe("Can't reach http://nas:9742 (NetworkError).");
    expect(helpFor("bad-token", "The server didn't accept the token.")).toEqual({
      title: "The server didn't accept the token.",
      tip: null,
      details: null,
    });
  });
});
