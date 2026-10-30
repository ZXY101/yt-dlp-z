import { isVideoInPlaylist } from "@/features/downloads/playlist-link";

describe("isVideoInPlaylist", () => {
  it.each([
    "https://www.youtube.com/watch?v=abc&list=PL123",
    "https://m.youtube.com/watch?list=PL123&v=abc&index=3",
    "https://music.youtube.com/watch?v=abc&list=RDabc",
    "https://youtu.be/abc?list=PL123",
    " https://youtube.com/watch?v=abc&list=PL123 ",
  ])("sees a video inside a playlist in %j", (url) => {
    expect(isVideoInPlaylist(url)).toBe(true);
  });

  it.each([
    "https://www.youtube.com/watch?v=abc",
    "https://youtu.be/abc",
    "https://www.youtube.com/playlist?list=PL123",
    "https://www.youtube.com/watch?list=PL123",
    "https://example.com/watch?v=abc&list=PL123",
    "not a link",
    "",
  ])("sees no video inside a playlist in %j", (url) => {
    expect(isVideoInPlaylist(url)).toBe(false);
  });
});
