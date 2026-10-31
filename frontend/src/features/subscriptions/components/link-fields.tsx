import { SelectField } from "@/components/form-field";
import { useCookieFiles } from "@/features/cookies";
import { type Preset, usePresets } from "@/features/presets";
import type { SubscriptionFormValues } from "@/features/subscriptions/form-values";

interface LinkFieldsProps {
  values: SubscriptionFormValues;
  onChange: (changes: Partial<SubscriptionFormValues>) => void;
}

function choicesFor(items: { id: number; name: string }[], noneLabel: string) {
  return [
    { value: "", label: noneLabel },
    ...items.map((item) => ({ value: String(item.id), label: item.name })),
  ];
}

function idOrNull(value: string) {
  return value ? Number(value) : null;
}

function StreamPresetField({ values, onChange }: LinkFieldsProps) {
  const presets = usePresets().data ?? [];
  // Live-stream presets first: they carry the recording settings.
  const sorted = presets.toSorted(
    (a: Preset, b: Preset) => Number(b.kind === "live") - Number(a.kind === "live"),
  );
  return (
    <SelectField
      label="Preset for live streams"
      hint="Streams and premieres record with this preset's options and recording settings. Default: the preset above, recorded like the default live-stream preset says."
      value={values.streamPresetId === null ? "" : String(values.streamPresetId)}
      choices={choicesFor(sorted, "Default")}
      onValueChange={(id) => onChange({ streamPresetId: idOrNull(id) })}
    />
  );
}

/** The preset and cookies file new downloads from this channel use. */
export function LinkFields({ values, onChange }: LinkFieldsProps) {
  const presets = usePresets().data ?? [];
  const cookieFiles = useCookieFiles().data ?? [];
  return (
    <>
      <SelectField
        label="Preset"
        hint="The download options for new uploads. Create presets on the Presets page."
        value={values.presetId === null ? "" : String(values.presetId)}
        choices={choicesFor(presets, "None (yt-dlp defaults)")}
        onValueChange={(id) => onChange({ presetId: idOrNull(id) })}
      />
      {values.contentTypes.includes("stream") && (
        <StreamPresetField values={values} onChange={onChange} />
      )}
      {cookieFiles.length > 0 && (
        <SelectField
          label="Cookies"
          hint="Overrides the preset's cookies. Needed for members-only videos."
          value={values.cookieId === null ? "" : String(values.cookieId)}
          choices={choicesFor(cookieFiles, "The preset's (if any)")}
          onValueChange={(id) => onChange({ cookieId: idOrNull(id) })}
        />
      )}
    </>
  );
}
