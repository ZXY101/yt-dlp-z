import type { components } from "@/api/generated/schema";

/** yt-dlp options keyed by long flag, the format the API stores for jobs and presets. */
export type OptionValues = NonNullable<components["schemas"]["JobCreate"]["options"]>;
export type OptionValue = OptionValues[string];
/** Media-server output: a folder per channel, with or without season folders. */
export type MediaLayout = NonNullable<components["schemas"]["JobCreate"]["media_layout"]>;
/** Whether downloads go through the proxy pool, and how a proxy is picked. */
export type ProxyMode = NonNullable<components["schemas"]["JobCreate"]["proxy_mode"]>;

/** Everything about how to download, shared by the download form and presets. */
export interface DownloadSettings {
  options: OptionValues;
  extraArgs: string;
  outputDir: string;
  cookieId: number | null;
  mediaLayout: MediaLayout | null;
  proxyMode: ProxyMode;
}

export const DEFAULT_SETTINGS: DownloadSettings = {
  options: { "--embed-metadata": true, "--embed-thumbnail": true },
  extraArgs: "",
  outputDir: "",
  cookieId: null,
  mediaLayout: null,
  proxyMode: "off",
};

export type Quality = "best" | "1080p" | "720p" | "audio" | "audio-mp3" | "custom";

const QUALITY_OPTIONS: Record<Exclude<Quality, "custom">, OptionValues> = {
  best: {},
  "1080p": { "--format-sort": ["res:1080"] },
  "720p": { "--format-sort": ["res:720"] },
  audio: { "--extract-audio": true },
  "audio-mp3": { "--extract-audio": true, "--audio-format": "mp3" },
};

const QUALITY_FLAGS = ["--format-sort", "--extract-audio", "--audio-format"];

export const QUALITY_CHOICES: { value: Quality; label: string }[] = [
  { value: "best", label: "Best available" },
  { value: "1080p", label: "Up to 1080p" },
  { value: "720p", label: "Up to 720p" },
  { value: "audio", label: "Audio only" },
  { value: "audio-mp3", label: "Audio only (MP3)" },
];

export const CUSTOM_QUALITY = { value: "custom", label: "Custom (see all options)" } as const;

/** Sets an option, or removes it when the value is undefined, false or empty. */
export function setOption(options: OptionValues, flag: string, value: OptionValue | undefined) {
  const next = { ...options };
  const isEmpty = value === undefined || value === false || value === "" || isEmptyList(value);
  if (isEmpty) {
    delete next[flag];
  } else {
    next[flag] = value;
  }
  return next;
}

function isEmptyList(value: OptionValue) {
  return Array.isArray(value) && value.length === 0;
}

function sameValue(a: OptionValue | undefined, b: OptionValue | undefined) {
  return JSON.stringify(a) === JSON.stringify(b);
}

/** Which quality choice the options match, or "custom" when set some other way. */
export function qualityOf(options: OptionValues): Quality {
  for (const [quality, expected] of Object.entries(QUALITY_OPTIONS)) {
    const matches = QUALITY_FLAGS.every((flag) => sameValue(options[flag], expected[flag]));
    if (matches) {
      return quality as Quality;
    }
  }
  return "custom";
}

export function withQuality(options: OptionValues, quality: Quality): OptionValues {
  if (quality === "custom") {
    return options;
  }
  const next = { ...options };
  for (const flag of QUALITY_FLAGS) {
    delete next[flag];
  }
  return { ...next, ...QUALITY_OPTIONS[quality] };
}

export function isOn(options: OptionValues, flag: string) {
  return options[flag] !== undefined && options[flag] !== false;
}

export function countSet(options: OptionValues, flags: string[]) {
  return flags.filter((flag) => isOn(options, flag)).length;
}

interface ApiDownloadSettings {
  options?: OptionValues;
  extra_args?: string;
  output_dir?: string | null;
  cookie_id?: number | null;
  media_layout?: MediaLayout | null;
  proxy_mode?: ProxyMode;
}

export function settingsFromApi(source: ApiDownloadSettings): DownloadSettings {
  return {
    options: source.options ?? {},
    extraArgs: source.extra_args ?? "",
    outputDir: source.output_dir ?? "",
    cookieId: source.cookie_id ?? null,
    mediaLayout: source.media_layout ?? null,
    proxyMode: source.proxy_mode ?? "off",
  };
}

export function settingsForApi(settings: DownloadSettings) {
  const template = settings.options["--output"];
  const options =
    typeof template === "string"
      ? setOption(settings.options, "--output", template.trim())
      : settings.options;
  return {
    options,
    extra_args: settings.extraArgs,
    output_dir: settings.outputDir.trim() || null,
    cookie_id: settings.cookieId,
    media_layout: settings.mediaLayout,
    proxy_mode: settings.proxyMode,
  };
}
