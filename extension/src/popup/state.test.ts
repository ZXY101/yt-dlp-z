import { describe, expect, it } from "vitest";
import type { MediaInfo, Preset } from "../lib/types.ts";
import {
  actionMode,
  buttonLabel,
  describeInfo,
  formatDuration,
  probeRequestFor,
  sendRequestFor,
  type PopupState,
} from "./state.ts";

const members: Preset = { id: 2, name: "Members", kind: "any", is_default: false, cookie_id: 7 };

function popup(overrides: Partial<PopupState> = {}): PopupState {
  return {
    url: "https://www.youtube.com/watch?v=abc",
    guess: "video",
    info: null,
    wholePlaylist: false,
    presetId: null,
    presets: [members],
    jobs: [],
    anotherCopy: false,
    ...overrides,
  };
}

function info(overrides: Partial<MediaInfo>): MediaInfo {
  return {
    kind: "video",
    title: "Title",
    uploader: null,
    thumbnail: null,
    duration: null,
    entry_count: null,
    starts_at: null,
    members_only: false,
    ...overrides,
  };
}

describe("probeRequestFor", () => {
  it("checks a video in a playlist alone unless the playlist is chosen", () => {
    expect(probeRequestFor(popup({ guess: "video-in-playlist" })).noPlaylist).toBe(true);
    const whole = popup({ guess: "video-in-playlist", wholePlaylist: true });
    expect(probeRequestFor(whole).noPlaylist).toBe(false);
  });

  it("uses the chosen preset's cookies", () => {
    expect(probeRequestFor(popup({ presetId: 2 })).cookieId).toBe(7);
    expect(probeRequestFor(popup()).cookieId).toBeNull();
  });
});

describe("sendRequestFor", () => {
  it("sends whole lists for playlists and channels", () => {
    expect(sendRequestFor(popup({ guess: "playlist" })).wholePlaylist).toBe(true);
    expect(
      sendRequestFor(popup({ guess: "unknown", info: info({ kind: "channel" }) })).wholePlaylist,
    ).toBe(true);
    expect(sendRequestFor(popup()).wholePlaylist).toBe(false);
  });

  it("follows the switch for a video in a playlist", () => {
    const state = popup({ guess: "video-in-playlist", info: info({ kind: "video" }) });
    expect(sendRequestFor(state).wholePlaylist).toBe(false);
    expect(sendRequestFor({ ...state, wholePlaylist: true }).wholePlaylist).toBe(true);
  });
});

describe("buttonLabel", () => {
  it.each([
    [popup(), "Download"],
    [popup({ info: info({ kind: "live" }) }), "Record"],
    [popup({ info: info({ kind: "upcoming" }) }), "Schedule recording"],
    [popup({ guess: "playlist" }), "Download all videos"],
    [
      popup({ guess: "playlist", info: info({ kind: "playlist", entry_count: 24 }) }),
      "Download 24 videos",
    ],
  ])("%#: %s", (state, label) => {
    expect(buttonLabel(state)).toBe(label);
  });
});

describe("actionMode and buttonLabel with a job", () => {
  const done = { id: 1, status: "completed", kind: "download" } as PopupState["jobs"][number];

  it("waits, disabled, while the link's job runs", () => {
    const running = popup({ jobs: [{ ...done, status: "running" }] });
    expect(actionMode(running)).toBe("busy");
    expect(buttonLabel(running)).toBe("Downloading…");
    const live = popup({ jobs: [{ ...done, status: "running", kind: "live" }] });
    expect(buttonLabel(live)).toBe("Recording…");
    expect(buttonLabel(popup({ jobs: [{ ...done, status: "queued" }] }))).toBe(
      "Waiting in the queue…",
    );
  });

  it("offers nothing for a finished download until another copy is asked for", () => {
    expect(actionMode(popup({ jobs: [done] }))).toBe("done");
    const another = popup({ jobs: [done], anotherCopy: true });
    expect(actionMode(another)).toBe("send");
    expect(buttonLabel(another)).toBe("Download");
  });

  it("sends again after a failure", () => {
    expect(actionMode(popup({ jobs: [{ ...done, status: "failed" }] }))).toBe("send");
  });
});

describe("describeInfo", () => {
  it("lists kind, length, uploader and members-only", () => {
    const video = info({ duration: 3725, uploader: "Someone", members_only: true });
    expect(describeInfo(video)).toBe("Video · 1:02:05 · Someone · Members only");
  });

  it("counts a playlist's videos", () => {
    expect(describeInfo(info({ kind: "playlist", entry_count: 3 }))).toBe("Playlist · 3 videos");
  });

  it("says a stream is live", () => {
    expect(describeInfo(info({ kind: "live", uploader: "Someone" }))).toBe("Live now · Someone");
  });
});

describe("formatDuration", () => {
  it("pads minutes and seconds", () => {
    expect(formatDuration(65)).toBe("1:05");
    expect(formatDuration(3600)).toBe("1:00:00");
  });
});
