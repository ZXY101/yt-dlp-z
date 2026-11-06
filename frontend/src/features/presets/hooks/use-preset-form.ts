import { useState } from "react";
import { useNavigate } from "react-router";

import { useRecordingFields } from "@/features/presets/components/recording-fields";
import { usePresets, useSavePreset } from "@/features/presets/api";
import { DEFAULT_RECORDING, kindRecords, recordingFor } from "@/features/presets/kinds";
import type { Preset, PresetKind } from "@/features/presets/types";
import { DEFAULT_SETTINGS, settingsForApi, settingsFromApi } from "@/lib/download-options";

export function usePresetForm(preset: Preset | null) {
  const [name, setName] = useState(preset?.name ?? "");
  const [kind, setKind] = useState<PresetKind>(preset?.kind ?? "any");
  const [isDefault, setIsDefault] = useState(preset?.is_default ?? false);
  const [settings, setSettings] = useState(preset ? settingsFromApi(preset) : DEFAULT_SETTINGS);
  const presets = usePresets().data ?? [];
  // An any-link preset saved without its own settings starts from those it records with now.
  const recording = useRecordingFields(preset ? recordingFor(preset, presets) : DEFAULT_RECORDING);
  const [nameError, setNameError] = useState<string>();
  const save = useSavePreset();
  const navigate = useNavigate();

  function check() {
    const error = name.trim() ? undefined : "Give the preset a name.";
    setNameError(error);
    // Recording fields only count for the kinds that show them.
    const recordingValid = !kindRecords(kind) || recording.check();
    return error === undefined && recordingValid;
  }

  function submit() {
    if (!check()) {
      return;
    }
    const body = {
      name: name.trim(),
      kind,
      is_default: isDefault,
      recording: kindRecords(kind) ? recording.values() : null,
      ...settingsForApi(settings),
    };
    save.mutate({ id: preset?.id ?? null, body }, { onSuccess: () => void navigate("/presets") });
  }

  return {
    fields: { name, kind, isDefault, settings },
    setters: { setName, setKind, setIsDefault, setSettings },
    recording,
    nameError,
    submit,
    save,
  };
}
