import { CheckboxField } from "@/components/checkbox-field";
import { SelectField } from "@/components/form-field";
import {
  CUSTOM_QUALITY,
  type OptionValues,
  QUALITY_CHOICES,
  isOn,
  qualityOf,
  setOption,
  withQuality,
} from "@/lib/download-options";

interface CommonOptionsProps {
  options: OptionValues;
  onChange: (options: OptionValues) => void;
}

/** The handful of choices most downloads need, mapped onto yt-dlp flags. */
export function CommonOptions({ options, onChange }: CommonOptionsProps) {
  const quality = qualityOf(options);
  const qualityChoices =
    quality === "custom" ? [...QUALITY_CHOICES, CUSTOM_QUALITY] : QUALITY_CHOICES;
  const embedsMetadata = isOn(options, "--embed-metadata") && isOn(options, "--embed-thumbnail");

  function setMetadata(on: boolean) {
    const withMetadata = setOption(options, "--embed-metadata", on);
    onChange(setOption(withMetadata, "--embed-thumbnail", on));
  }

  return (
    <div className="space-y-4">
      <SelectField
        label="Quality"
        value={quality}
        choices={qualityChoices}
        onValueChange={(choice) => onChange(withQuality(options, choice))}
      />
      <fieldset className="space-y-1">
        <legend className="sr-only">Extras</legend>
        <CheckboxField
          label="Embed subtitles"
          checked={isOn(options, "--embed-subs")}
          onCheckedChange={(on) => onChange(setOption(options, "--embed-subs", on))}
        />
        <CheckboxField
          label="Embed thumbnail and metadata"
          description="Title, uploader, date and cover art inside the file."
          checked={embedsMetadata}
          onCheckedChange={setMetadata}
        />
        <CheckboxField
          label="Remove sponsor segments"
          description="Cuts sponsored sections using SponsorBlock."
          checked={isOn(options, "--sponsorblock-remove")}
          onCheckedChange={(on) =>
            onChange(setOption(options, "--sponsorblock-remove", on ? ["sponsor"] : undefined))
          }
        />
      </fieldset>
    </div>
  );
}
