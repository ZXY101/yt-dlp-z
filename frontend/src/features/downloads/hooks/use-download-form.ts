import { useState } from "react";
import { useNavigate } from "react-router";

import { useCreateJob } from "@/features/downloads/api";
import { usePresetChoice } from "@/features/downloads/hooks/use-preset-choice";
import { validateUrl } from "@/features/downloads/validate-url";
import { DEFAULT_SETTINGS, type DownloadSettings, settingsForApi } from "@/lib/download-options";

export function useDownloadForm() {
  const [url, setUrl] = useState("");
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  // Remounts the option fields when a preset replaces the settings wholesale,
  // so fields that keep their own text (one value per line) start fresh.
  const [settingsVersion, setSettingsVersion] = useState(0);
  const [urlError, setUrlError] = useState<string>();
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
    const body = { url: url.trim(), ...settingsForApi(settings) };
    createJob.mutate(body, { onSuccess: () => void navigate("/queue") });
  }

  return {
    url,
    setUrl,
    settings,
    setSettings,
    settingsVersion,
    presetChoice,
    urlError,
    submit,
    createJob,
  };
}

export type DownloadForm = ReturnType<typeof useDownloadForm>;
