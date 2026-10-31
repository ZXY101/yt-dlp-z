import { useState } from "react";

import {
  type Preset,
  type PresetKind,
  defaultPresetFor,
  recordingFor,
  sortForKind,
  usePresets,
} from "@/features/presets";
import { DEFAULT_SETTINGS, type DownloadSettings, settingsFromApi } from "@/lib/download-options";

/** The preset picker. Choosing a preset copies its settings into the form. `linkKind`: what
 * the checked link is; null while it isn't known. */
export function usePresetChoice(
  applySettings: (settings: DownloadSettings) => void,
  linkKind: PresetKind | null,
) {
  const presets = usePresets();
  const [presetId, setPresetId] = useState("");
  const [pickedFor, setPickedFor] = useState<PresetKind | null>(null);
  const list = presets.data ?? [];
  const kind = linkKind ?? pickedFor ?? "any";

  function apply(preset: Preset | undefined) {
    setPresetId(preset ? String(preset.id) : "");
    applySettings(preset ? settingsFromApi(preset) : DEFAULT_SETTINGS);
  }

  function choose(id: string) {
    apply(list.find((item) => String(item.id) === id));
  }

  // Pick the default preset when the list arrives and whenever the checked link turns out to
  // be another kind, keeping the current one if that kind has no default (adjusting state
  // during render rather than in an effect, so the form never flashes the old settings).
  if (presets.data && kind !== pickedFor) {
    setPickedFor(kind);
    const preset = defaultPresetFor(presets.data, kind);
    if (preset && String(preset.id) !== presetId) {
      apply(preset);
    }
  }

  const selected = list.find((item) => String(item.id) === presetId);
  return {
    presets: sortForKind(list, kind),
    presetId,
    choose,
    recording: recordingFor(selected, list),
  };
}
