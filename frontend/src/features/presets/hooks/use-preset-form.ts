import { useState } from "react";
import { useNavigate } from "react-router";

import { useSavePreset } from "@/features/presets/api";
import type { Preset } from "@/features/presets/types";
import { DEFAULT_SETTINGS, settingsForApi, settingsFromApi } from "@/lib/download-options";

export function usePresetForm(preset: Preset | null) {
  const [name, setName] = useState(preset?.name ?? "");
  const [isDefault, setIsDefault] = useState(preset?.is_default ?? false);
  const [settings, setSettings] = useState(preset ? settingsFromApi(preset) : DEFAULT_SETTINGS);
  const [nameError, setNameError] = useState<string>();
  const save = useSavePreset();
  const navigate = useNavigate();

  function submit() {
    const error = name.trim() ? undefined : "Give the preset a name.";
    setNameError(error);
    if (error) {
      return;
    }
    const body = { name: name.trim(), is_default: isDefault, ...settingsForApi(settings) };
    save.mutate({ id: preset?.id ?? null, body }, { onSuccess: () => void navigate("/presets") });
  }

  return {
    fields: { name, isDefault, settings },
    setters: { setName, setIsDefault, setSettings },
    nameError,
    submit,
    save,
  };
}
