import type { components } from "@/api/generated/schema";

type OptionSpec = components["schemas"]["OptionSpec"];

function option(flag: string, changes: Partial<OptionSpec> = {}): OptionSpec {
  return {
    flag,
    aliases: [],
    short: [],
    kind: "flag",
    repeatable: false,
    metavar: null,
    choices: null,
    help: `Help for ${flag}`,
    blocked_reason: null,
    ...changes,
  };
}

/** A small slice of yt-dlp's option schema with one option of every kind. */
export const FAKE_SCHEMA: components["schemas"]["OptionSchema"] = {
  ytdlp_version: "2026.10.26",
  groups: [
    {
      title: "Network Options",
      options: [
        option("--proxy", { kind: "string", metavar: "URL", help: "Use the specified HTTP proxy" }),
        option("--force-ipv4", { short: ["-4"] }),
      ],
    },
    {
      title: "Download Options",
      options: [
        option("--limit-rate", { kind: "string", metavar: "RATE", aliases: ["-r"] }),
        option("--retries", { kind: "number", metavar: "RETRIES" }),
        option("--exec", { kind: "string", blocked_reason: "It runs shell commands." }),
      ],
    },
    {
      title: "Post-Processing Options",
      options: [
        option("--embed-subs"),
        option("--embed-metadata"),
        option("--embed-thumbnail"),
        option("--audio-format", { kind: "string", metavar: "FORMAT" }),
        option("--sponsorblock-remove", { kind: "string", repeatable: true }),
        option("--remux-video", { kind: "choice", choices: ["mp4", "mkv"] }),
      ],
    },
  ],
};
