import { useRef, useState } from "react";
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

interface JobBodyInput {
  url: string;
  media: MediaInfo;
  settings: DownloadSettings;
  fromStart: boolean;
  wholePlaylist: boolean;
  videoInPlaylist: boolean;
}

function jobBody(input: JobBodyInput): JobCreate {
  const { settings, wholePlaylist } = input;
  const options = input.videoInPlaylist
    ? withPlaylistChoice(settings.options, wholePlaylist)
    : settings.options;
  return {
    url: input.url.trim(),
    title: input.media.title,
    recording: recordingFor(input.media, input.fromStart),
    ...settingsForApi({ ...settings, options }),
  };
}

/** The link field. A pasted link is checked at once; typing waits for a pause. */
function useUrlInput(onChange: () => void) {
  const [url, setUrl] = useState("");
  const [pastedUrl, setPastedUrl] = useState<string | null>(null);
  const pasting = useRef(false);

  function changeUrl(next: string) {
    setUrl(next);
    setPastedUrl(pasting.current ? next : null);
    pasting.current = false;
    onChange();
  }

  /** Called before the change a paste causes. */
  function markPaste() {
    pasting.current = true;
  }

  return { url, changeUrl, markPaste, pasted: url === pastedUrl };
}

export function useDownloadForm() {
  const { settings, setSettings, settingsVersion, presetChoice } = useSettingsState();
  const [wholePlaylist, setWholePlaylist] = useState(false);
  // null: what the recording settings suggest for this stream.
  const [fromStartChoice, setFromStart] = useState<boolean | null>(null);
  const { url, changeUrl, markPaste, pasted } = useUrlInput(() => setFromStart(null));
  const videoInPlaylist = isVideoInPlaylist(url);
  const noPlaylist = videoInPlaylist && !wholePlaylist;
  const check = useLinkCheck({
    url,
    cookieId: settings.cookieId,
    noPlaylist,
    immediate: pasted,
  });
  const media = readyMedia(check);
  const fromStart = fromStartChoice ?? media?.record_from_start ?? true;
  const createJob = useCreateJob();
  const navigate = useNavigate();

  function submit() {
    if (!media) {
      return;
    }
    const body = jobBody({ url, media, settings, fromStart, wholePlaylist, videoInPlaylist });
    createJob.mutate(body, { onSuccess: () => void navigate("/queue") });
  }

  return {
    url,
    setUrl: changeUrl,
    markPaste,
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
