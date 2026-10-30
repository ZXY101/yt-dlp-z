import { CheckboxField } from "@/components/checkbox-field";
import { SelectField } from "@/components/form-field";
import type { DownloadForm } from "@/features/downloads/hooks/use-download-form";
import { QUALITY_CHOICES } from "@/features/downloads/options";

export function CommonOptions({ form }: { form: DownloadForm }) {
  const { choices, updateChoices } = form;
  return (
    <div className="space-y-4">
      <SelectField
        label="Quality"
        value={choices.quality}
        choices={QUALITY_CHOICES}
        onValueChange={(quality) => updateChoices({ quality })}
      />
      <fieldset className="space-y-1">
        <legend className="sr-only">Extras</legend>
        <CheckboxField
          label="Embed subtitles"
          checked={choices.embedSubtitles}
          onCheckedChange={(embedSubtitles) => updateChoices({ embedSubtitles })}
        />
        <CheckboxField
          label="Embed thumbnail and metadata"
          description="Title, uploader, date and cover art inside the file."
          checked={choices.embedMetadata}
          onCheckedChange={(embedMetadata) => updateChoices({ embedMetadata })}
        />
        <CheckboxField
          label="Remove sponsor segments"
          description="Cuts sponsored sections using SponsorBlock."
          checked={choices.removeSponsors}
          onCheckedChange={(removeSponsors) => updateChoices({ removeSponsors })}
        />
      </fieldset>
    </div>
  );
}
