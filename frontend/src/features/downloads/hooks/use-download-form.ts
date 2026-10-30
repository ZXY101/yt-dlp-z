import { useState } from "react";
import { useNavigate } from "react-router";

import { useCreateJob } from "@/features/downloads/api";
import { usePresetChoice } from "@/features/downloads/hooks/use-preset-choice";
import { playlistLinkKind } from "@/features/downloads/playlist-link";
import { validateUrl } from "@/features/downloads/validate-url";
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

export function useDownloadForm() {
  const [url, setUrl] = useState("");
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  // Remounts the option fields when a preset replaces the settings wholesale,
  // so fields that keep their own text (one value per line) start fresh.
  const [settingsVersion, setSettingsVersion] = useState(0);
  const [urlError, setUrlError] = useState<string>();
  const [wholePlaylist, setWholePlaylist] = useState(false);
  const playlistKind = playlistLinkKind(url);
  const createJob = useCreateJob();
  const navigate = useNavigate();

  function replaceSettings(next: DownloadSettings) {
    setSettings(next);
    setSettingsVersion((version) => version + 1);
  }

  const presetChoice = usePresetChoice(replaceSettings);

  function submit() {
    const error = validateUrl(url);
    setUrlError(error);
    if (error) {
      return;
    }
    const options =
      playlistKind === "video-in-playlist"
        ? withPlaylistChoice(settings.options, wholePlaylist)
        : settings.options;
    const body = { url: url.trim(), ...settingsForApi({ ...settings, options }) };
    createJob.mutate(body, { onSuccess: () => void navigate("/queue") });
  }

  return {
    url,
    setUrl,
    settings,
    setSettings,
    settingsVersion,
    presetChoice,
    playlistKind,
    wholePlaylist,
    setWholePlaylist,
    urlError,
    submit,
    createJob,
  };
}

export type DownloadForm = ReturnType<typeof useDownloadForm>;
