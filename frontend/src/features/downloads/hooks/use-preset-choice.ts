import { useState } from "react";

import { type Preset, usePresets } from "@/features/presets";
import { DEFAULT_SETTINGS, type DownloadSettings, settingsFromApi } from "@/lib/download-options";

/** The preset picker. Choosing a preset copies its settings into the form. */
export function usePresetChoice(applySettings: (settings: DownloadSettings) => void) {
  const presets = usePresets();
  const [presetId, setPresetId] = useState("");
  const [loaded, setLoaded] = useState(false);

  function choose(id: string) {
    const preset = presets.data?.find((item) => String(item.id) === id);
    setPresetId(preset ? id : "");
    applySettings(preset ? settingsFromApi(preset) : DEFAULT_SETTINGS);
  }

  // Pick the default preset once, when the list first arrives (adjusting state
  // during render rather than in an effect, so the form never flashes the defaults).
  if (presets.data && !loaded) {
    setLoaded(true);
    const preset = presets.data.find((item: Preset) => item.is_default);
    if (preset) {
      setPresetId(String(preset.id));
      applySettings(settingsFromApi(preset));
    }
  }

  return { presets: presets.data ?? [], presetId, choose };
}
