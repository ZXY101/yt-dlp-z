import { describeError } from "@/api/errors";
import { DownloadSettingsFields } from "@/components/download-options/download-settings-fields";
import { FormError } from "@/components/form-error";
import { FormField, SelectField } from "@/components/form-field";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { useCookieFiles } from "@/features/cookies";
import { type DownloadForm, useDownloadForm } from "@/features/downloads/hooks/use-download-form";
import { SystemWarnings } from "@/features/system";

function PresetField({ choice }: { choice: DownloadForm["presetChoice"] }) {
  if (choice.presets.length === 0) {
    return null;
  }
  const choices = [
    { value: "", label: "None" },
    ...choice.presets.map((preset) => ({ value: String(preset.id), label: preset.name })),
  ];
  return (
    <SelectField
      label="Preset"
      hint="Fills in the options below. You can still change them for this download."
      value={choice.presetId}
      choices={choices}
      onValueChange={choice.choose}
    />
  );
}

export function DownloadPage() {
  const form = useDownloadForm();
  const cookieFiles = useCookieFiles().data ?? [];

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    form.submit();
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader title="Download" />
      <SystemWarnings />
      <form className="space-y-6" onSubmit={handleSubmit} noValidate>
        <FormError message={form.createJob.isError ? describeError(form.createJob.error) : null} />
        <FormField
          label="Link"
          type="url"
          inputMode="url"
          placeholder="https://www.youtube.com/watch?v=…"
          hint="A video, playlist or channel from any site yt-dlp supports."
          required
          value={form.url}
          error={form.urlError}
          onChange={(event) => form.setUrl(event.target.value)}
        />
        <PresetField choice={form.presetChoice} />
        <DownloadSettingsFields
          key={form.settingsVersion}
          value={form.settings}
          onChange={form.setSettings}
          cookieFiles={cookieFiles}
        />
        <Button
          type="submit"
          size="lg"
          className="h-10 w-full sm:w-auto"
          disabled={form.createJob.isPending}
        >
          {form.createJob.isPending ? "Starting…" : "Download"}
        </Button>
      </form>
    </div>
  );
}
