import { useRef, useState } from "react";
import { useNavigate } from "react-router";

import { useCreateJob } from "@/features/downloads/api";
import { type LinkCheck, useLinkCheck } from "@/features/downloads/hooks/use-link-check";
import { usePresetChoice } from "@/features/downloads/hooks/use-preset-choice";
import {
  type RecordingChoiceState,
  useRecordingChoice,
} from "@/features/downloads/hooks/use-recording-choice";
import { isVideoInPlaylist } from "@/features/downloads/playlist-link";
import type { JobCreate, MediaInfo } from "@/features/downloads/types";
import { type PresetKind, presetKindFor } from "@/features/presets";
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

function readyMedia(check: LinkCheck) {
  return check.status === "ready" ? check.media : undefined;
}

function useSettingsState(linkKind: PresetKind | null) {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  // Remounts the option fields when a preset replaces the settings wholesale,
  // so fields that keep their own text (one value per line) start fresh.
  const [settingsVersion, setSettingsVersion] = useState(0);

  function replaceSettings(next: DownloadSettings) {
    setSettings(next);
    setSettingsVersion((version) => version + 1);
  }

  const presetChoice = usePresetChoice(replaceSettings, linkKind);
  return { settings, setSettings, settingsVersion, presetChoice };
}

interface JobBodyInput {
  url: string;
  media: MediaInfo;
  settings: DownloadSettings;
  recording: JobCreate["recording"];
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
    recording: input.recording,
    ...settingsForApi({ ...settings, options }),
  };
}

/** The link field. A pasted link is checked at once; typing waits for a pause. */
function useUrlInput() {
  const [url, setUrl] = useState("");
  const [pastedUrl, setPastedUrl] = useState<string | null>(null);
  const pasting = useRef(false);

  function changeUrl(next: string) {
    setUrl(next);
    setPastedUrl(pasting.current ? next : null);
    pasting.current = false;
  }

  /** Called before the change a paste causes. */
  function markPaste() {
    pasting.current = true;
  }

  return { url, changeUrl, markPaste, pasted: url === pastedUrl };
}

/** The checked link, and the settings that depend on what it is. */
function useCheckedLink(cookieId: number | null) {
  const [wholePlaylist, setWholePlaylist] = useState(false);
  const { url, changeUrl, markPaste, pasted } = useUrlInput();
  const videoInPlaylist = isVideoInPlaylist(url);
  const noPlaylist = videoInPlaylist && !wholePlaylist;
  const check = useLinkCheck({ url, cookieId, noPlaylist, immediate: pasted });
  return { url, changeUrl, markPaste, check, videoInPlaylist, wholePlaylist, setWholePlaylist };
}

export function useDownloadForm() {
  // The cookies field is part of the settings, and the link check needs it; the preset
  // picker in turn needs to know what the link is. The kind is kept from the last check.
  const [linkKind, setLinkKind] = useState<PresetKind | null>(null);
  const { settings, setSettings, settingsVersion, presetChoice } = useSettingsState(linkKind);
  const link = useCheckedLink(settings.cookieId);
  const { url, check, videoInPlaylist, wholePlaylist } = link;
  const media = readyMedia(check);
  const mediaKind = media ? presetKindFor(media.kind) : null;
  if (mediaKind !== null && mediaKind !== linkKind) {
    setLinkKind(mediaKind);
  }
  const recording: RecordingChoiceState = useRecordingChoice({
    media,
    checkedAt: check.status === "ready" ? check.checkedAt : 0,
    recording: presetChoice.recording,
    presetId: presetChoice.presetId,
  });
  const createJob = useCreateJob();
  const navigate = useNavigate();

  function submit() {
    if (!media || !recording.check()) {
      return;
    }
    const body = jobBody({
      url,
      media,
      settings,
      recording: recording.request(),
      wholePlaylist,
      videoInPlaylist,
    });
    createJob.mutate(body, { onSuccess: () => void navigate("/queue") });
  }

  return {
    url,
    setUrl: link.changeUrl,
    markPaste: link.markPaste,
    settings,
    setSettings,
    settingsVersion,
    presetChoice,
    check,
    media,
    videoInPlaylist,
    wholePlaylist,
    setWholePlaylist: link.setWholePlaylist,
    recording,
    submit,
    createJob,
  };
}

export type DownloadForm = ReturnType<typeof useDownloadForm>;
