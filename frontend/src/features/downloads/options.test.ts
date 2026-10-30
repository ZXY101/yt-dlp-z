import { DEFAULT_CHOICES, buildOptions, validateUrl } from "@/features/downloads/options";

describe("buildOptions", () => {
  it("embeds metadata by default and nothing else", () => {
    expect(buildOptions(DEFAULT_CHOICES)).toEqual({
      "--embed-metadata": true,
      "--embed-thumbnail": true,
    });
  });

  it("maps every choice onto yt-dlp flags", () => {
    const options = buildOptions({
      quality: "audio-mp3",
      embedSubtitles: true,
      embedMetadata: false,
      removeSponsors: true,
      outputTemplate: "  %(uploader)s/%(title)s.%(ext)s  ",
    });
    expect(options).toEqual({
      "--extract-audio": true,
      "--audio-format": "mp3",
      "--embed-subs": true,
      "--sponsorblock-remove": ["sponsor"],
      "--output": "%(uploader)s/%(title)s.%(ext)s",
    });
  });

  it.each([
    ["1080p", { "--format-sort": ["res:1080"] }],
    ["720p", { "--format-sort": ["res:720"] }],
    ["audio", { "--extract-audio": true }],
  ] as const)("quality %s", (quality, expected) => {
    expect(buildOptions({ ...DEFAULT_CHOICES, quality, embedMetadata: false })).toEqual(expected);
  });
});

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
