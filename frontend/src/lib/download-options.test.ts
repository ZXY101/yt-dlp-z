import {
  type OptionValues,
  DEFAULT_SETTINGS,
  countSet,
  isOn,
  qualityOf,
  setOption,
  settingsForApi,
  settingsFromApi,
  withQuality,
} from "@/lib/download-options";

describe("setOption", () => {
  it("adds and replaces values", () => {
    expect(setOption({}, "--limit-rate", "2M")).toEqual({ "--limit-rate": "2M" });
    expect(setOption({ "--retries": "3" }, "--retries", "5")).toEqual({ "--retries": "5" });
  });

  it.each([undefined, false, "", []])("removes the option for %j", (value) => {
    expect(setOption({ "--x": true, "--y": "1" }, "--x", value)).toEqual({ "--y": "1" });
  });
});

describe("quality", () => {
  it.each([
    [{}, "best"],
    [{ "--format-sort": ["res:1080"] }, "1080p"],
    [{ "--format-sort": ["res:720"], "--embed-subs": true }, "720p"],
    [{ "--extract-audio": true }, "audio"],
    [{ "--extract-audio": true, "--audio-format": "mp3" }, "audio-mp3"],
    [{ "--format-sort": ["res:480"] }, "custom"],
    [{ "--extract-audio": true, "--audio-format": "opus" }, "custom"],
  ] as [OptionValues, string][])("recognises %j as %s", (options, quality) => {
    expect(qualityOf(options)).toBe(quality);
  });

  it("replaces only the quality flags", () => {
    const options = { "--extract-audio": true, "--audio-format": "mp3", "--embed-subs": true };
    expect(withQuality(options, "1080p")).toEqual({
      "--format-sort": ["res:1080"],
      "--embed-subs": true,
    });
    expect(withQuality(options, "custom")).toBe(options);
  });
});

it("counts options that are switched on or have a value", () => {
  const options = { "--a": true, "--b": "x", "--c": false };
  expect(isOn(options, "--b")).toBe(true);
  expect(isOn(options, "--c")).toBe(false);
  expect(countSet(options, ["--a", "--b", "--c", "--d"])).toBe(2);
});

describe("API conversion", () => {
  it("trims the folder and file name template and round-trips", () => {
    const settings = {
      options: { "--output": "  %(title)s.%(ext)s  ", "--embed-subs": true },
      extraArgs: "--limit-rate 2M",
      outputDir: "  music  ",
      cookieId: 3,
      mediaLayout: "season" as const,
    };
    const body = settingsForApi(settings);
    expect(body).toEqual({
      options: { "--output": "%(title)s.%(ext)s", "--embed-subs": true },
      extra_args: "--limit-rate 2M",
      output_dir: "music",
      cookie_id: 3,
      media_layout: "season",
    });
    expect(settingsFromApi(body)).toEqual({ ...settings, ...settingsFromApi(body) });
    expect(settingsFromApi({})).toEqual({
      options: {},
      extraArgs: "",
      outputDir: "",
      cookieId: null,
      mediaLayout: null,
    });
  });

  it("sends no folder when it is blank", () => {
    expect(settingsForApi({ ...DEFAULT_SETTINGS, outputDir: "  " }).output_dir).toBeNull();
  });
});
