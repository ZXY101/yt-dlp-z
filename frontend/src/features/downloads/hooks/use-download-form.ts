import { useState } from "react";
import { useNavigate } from "react-router";

import { useCreateJob } from "@/features/downloads/api";
import { type LinkCheck, useLinkCheck } from "@/features/downloads/hooks/use-link-check";
import { usePresetChoice } from "@/features/downloads/hooks/use-preset-choice";
import { isVideoInPlaylist } from "@/features/downloads/playlist-link";
import type { JobCreate, MediaInfo } from "@/features/downloads/types";
import {
  DEFAULT_SETTINGS,
  type DownloadSettings,
  type OptionValues,
  setOption,
  settingsForApi,
} from "@/lib/download-options";

/** For a video inside a playlist, the radio choice decides; it overrides either flag. */
function withPlaylistChoice(options: OptionValues, wholePlaylist: boolean) {
  const withYes = setOption(options, "--yes-playlist", wholePlaylist);
  return setOption(withYes, "--no-playlist", !wholePlaylist);
}

function isStream(media: MediaInfo | undefined) {
  return media?.kind === "live" || media?.kind === "upcoming";
}

function recordingFor(media: MediaInfo, fromStart: boolean): JobCreate["recording"] {
  if (!isStream(media)) {
    return null;
  }
  // Upcoming streams are always recorded from their start.
  return { from_start: media.kind === "upcoming" || fromStart, starts_at: media.starts_at };
}

function readyMedia(check: LinkCheck) {
  return check.status === "ready" ? check.media : undefined;
}

function useSettingsState() {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  // Remounts the option fields when a preset replaces the settings wholesale,
  // so fields that keep their own text (one value per line) start fresh.
  const [settingsVersion, setSettingsVersion] = useState(0);

  function replaceSettings(next: DownloadSettings) {
    setSettings(next);
    setSettingsVersion((version) => version + 1);
  }

  const presetChoice = usePresetChoice(replaceSettings);
  return { settings, setSettings, settingsVersion, presetChoice };
}

export function useDownloadForm() {
  const [url, setUrl] = useState("");
  const { settings, setSettings, settingsVersion, presetChoice } = useSettingsState();
  const [wholePlaylist, setWholePlaylist] = useState(false);
  // null: what the recording settings suggest for this stream.
  const [fromStartChoice, setFromStart] = useState<boolean | null>(null);
  const videoInPlaylist = isVideoInPlaylist(url);
  const noPlaylist = videoInPlaylist && !wholePlaylist;
  const check = useLinkCheck({ url, cookieId: settings.cookieId, noPlaylist });
  const media = readyMedia(check);
  const fromStart = fromStartChoice ?? media?.record_from_start ?? true;
  const createJob = useCreateJob();
  const navigate = useNavigate();

  function changeUrl(next: string) {
    setUrl(next);
    setFromStart(null);
  }

  function submit() {
    if (!media) {
      return;
    }
    const options = videoInPlaylist
      ? withPlaylistChoice(settings.options, wholePlaylist)
      : settings.options;
    const body: JobCreate = {
      url: url.trim(),
      title: media.title,
      recording: recordingFor(media, fromStart),
      ...settingsForApi({ ...settings, options }),
    };
    createJob.mutate(body, { onSuccess: () => void navigate("/queue") });
  }

  return {
    url,
    setUrl: changeUrl,
    settings,
    setSettings,
    settingsVersion,
    presetChoice,
    check,
    media,
    videoInPlaylist,
    wholePlaylist,
    setWholePlaylist,
    fromStart,
    setFromStart,
    submit,
    createJob,
  };
}

export type DownloadForm = ReturnType<typeof useDownloadForm>;
