import { playlistLinkKind } from "@/features/downloads/playlist-link";

describe("playlistLinkKind", () => {
  it.each([
    "https://www.youtube.com/watch?v=abc&list=PL123",
    "https://m.youtube.com/watch?list=PL123&v=abc&index=3",
    "https://music.youtube.com/watch?v=abc&list=RDabc",
    "https://youtu.be/abc?list=PL123",
    " https://youtube.com/watch?v=abc&list=PL123 ",
  ])("sees a video inside a playlist in %j", (url) => {
    expect(playlistLinkKind(url)).toBe("video-in-playlist");
  });

  it.each([
    "https://www.youtube.com/playlist?list=PL123",
    "https://music.youtube.com/playlist?list=OLAK5uy",
  ])("sees a playlist in %j", (url) => {
    expect(playlistLinkKind(url)).toBe("playlist");
  });

  it.each([
    "https://www.youtube.com/@someone",
    "https://www.youtube.com/@someone/videos",
    "https://www.youtube.com/channel/UC123/streams",
    "https://www.youtube.com/c/Someone",
    "https://www.youtube.com/user/someone/",
  ])("sees a channel in %j", (url) => {
    expect(playlistLinkKind(url)).toBe("channel");
  });

  it.each([
    "https://www.youtube.com/watch?v=abc",
    "https://youtu.be/abc",
    "https://www.youtube.com/shorts/abc",
    "https://www.youtube.com/playlist",
    "https://www.youtube.com/watch?list=PL123",
    "https://example.com/watch?v=abc&list=PL123",
    "https://example.com/@someone",
    "not a link",
    "",
  ])("sees no playlist in %j", (url) => {
    expect(playlistLinkKind(url)).toBeUndefined();
  });
});
