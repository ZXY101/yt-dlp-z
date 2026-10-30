import type { JobOptions } from "@/features/downloads/types";

export type Quality = "best" | "1080p" | "720p" | "audio" | "audio-mp3";

export const QUALITY_CHOICES: { value: Quality; label: string }[] = [
  { value: "best", label: "Best available" },
  { value: "1080p", label: "Up to 1080p" },
  { value: "720p", label: "Up to 720p" },
  { value: "audio", label: "Audio only" },
  { value: "audio-mp3", label: "Audio only (MP3)" },
];

const QUALITY_OPTIONS: Record<Quality, JobOptions> = {
  best: {},
  "1080p": { "--format-sort": ["res:1080"] },
  "720p": { "--format-sort": ["res:720"] },
  audio: { "--extract-audio": true },
  "audio-mp3": { "--extract-audio": true, "--audio-format": "mp3" },
};

export interface CommonChoices {
  quality: Quality;
  embedSubtitles: boolean;
  embedMetadata: boolean;
  removeSponsors: boolean;
  outputTemplate: string;
}

export const DEFAULT_CHOICES: CommonChoices = {
  quality: "best",
  embedSubtitles: false,
  embedMetadata: true,
  removeSponsors: false,
  outputTemplate: "",
};

/** Maps the curated form choices onto yt-dlp flags (the same keys the backend validates). */
export function buildOptions(choices: CommonChoices): JobOptions {
  const options: JobOptions = { ...QUALITY_OPTIONS[choices.quality] };
  if (choices.embedSubtitles) {
    options["--embed-subs"] = true;
  }
  if (choices.embedMetadata) {
    options["--embed-metadata"] = true;
    options["--embed-thumbnail"] = true;
  }
  if (choices.removeSponsors) {
    options["--sponsorblock-remove"] = ["sponsor"];
  }
  const template = choices.outputTemplate.trim();
  if (template) {
    options["--output"] = template;
  }
  return options;
}

export function validateUrl(url: string): string | undefined {
  const trimmed = url.trim();
  if (!trimmed) {
    return "Paste a link to a video, playlist or channel.";
  }
  if (!/^https?:\/\/\S+$/i.test(trimmed)) {
    return "Use a full link starting with http:// or https://.";
  }
  return undefined;
}
