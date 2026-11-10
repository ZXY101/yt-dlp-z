import { describe, expect, it } from "vitest";
import { guessLink, isVideoPage, isWholeList } from "./link-guess.ts";

describe("guessLink", () => {
  it.each([
    ["https://www.youtube.com/watch?v=abc", "video"],
    ["https://m.youtube.com/watch?v=abc&t=10", "video"],
    ["https://www.youtube.com/watch?v=abc&list=PL1", "video-in-playlist"],
    ["https://www.youtube.com/playlist?list=PL1", "playlist"],
    ["https://www.youtube.com/shorts/abc", "video"],
    ["https://www.youtube.com/live/abc", "video"],
    ["https://www.youtube.com/@someone", "channel"],
    ["https://www.youtube.com/@someone/streams", "channel"],
    ["https://www.youtube.com/channel/UC123", "channel"],
    ["https://music.youtube.com/watch?v=abc", "video"],
    ["https://youtu.be/abc", "video"],
    ["https://youtu.be/abc?list=PL1", "video-in-playlist"],
    ["https://vimeo.com/123456", "video"],
    ["https://www.youtube.com/feed/subscriptions", "unknown"],
    ["https://example.org/video.mp4", "unknown"],
    ["chrome://extensions", "unsupported"],
    ["about:blank", "unsupported"],
    ["", "unsupported"],
  ])("%s → %s", (url, expected) => {
    expect(guessLink(url)).toBe(expected);
  });
});

describe("isWholeList", () => {
  it("is true for playlists and channels only", () => {
    expect(isWholeList("playlist")).toBe(true);
    expect(isWholeList("channel")).toBe(true);
    expect(isWholeList("video-in-playlist")).toBe(false);
    expect(isWholeList("unknown")).toBe(false);
  });
});

describe("isVideoPage", () => {
  it("is true for single videos, also opened from a playlist", () => {
    expect(isVideoPage("https://www.youtube.com/watch?v=abc")).toBe(true);
    expect(isVideoPage("https://www.youtube.com/watch?v=abc&list=PL1")).toBe(true);
  });

  it("leaves lists, unknown sites and browser pages alone", () => {
    expect(isVideoPage("https://www.youtube.com/playlist?list=PL1")).toBe(false);
    expect(isVideoPage("https://www.youtube.com/@someone")).toBe(false);
    expect(isVideoPage("https://example.org/")).toBe(false);
    expect(isVideoPage("chrome://newtab")).toBe(false);
  });
});
