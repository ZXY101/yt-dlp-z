import { describeError } from "@/api/errors";
import { DownloadSettingsFields } from "@/components/download-options/download-settings-fields";
import { FormError } from "@/components/form-error";
import { FormField, SelectField } from "@/components/form-field";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { useCookieFiles } from "@/features/cookies";
import { useProxies } from "@/features/proxies";
import { MediaPreview } from "@/features/downloads/components/media-preview";
import { PlaylistChoice } from "@/features/downloads/components/playlist-choice";
import { RecordingChoice } from "@/features/downloads/components/recording-choice";
import { type DownloadForm, useDownloadForm } from "@/features/downloads/hooks/use-download-form";
import { PRESET_KIND_LABELS, type Preset } from "@/features/presets";
import { SystemWarnings } from "@/features/system";

/** e.g. "Concerts (live streams)"; presets for any link, or named after their kind, show
 * just their name. */
function presetLabel(preset: Preset) {
  const kind = PRESET_KIND_LABELS[preset.kind].toLowerCase();
  if (preset.kind === "any" || preset.name.toLowerCase() === kind) {
    return preset.name;
  }
  return `${preset.name} (${kind})`;
}

function PresetField({ choice }: { choice: DownloadForm["presetChoice"] }) {
  if (choice.presets.length === 0) {
    return null;
  }
  const choices = [
    { value: "", label: "None" },
    ...choice.presets.map((preset) => ({ value: String(preset.id), label: presetLabel(preset) })),
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

function submitLabel(form: DownloadForm) {
  if (form.createJob.isPending) {
    return "Starting…";
  }
  const labels = { live: "Record", upcoming: "Schedule recording" };
  const kind = form.media?.kind;
  return kind === "live" || kind === "upcoming" ? labels[kind] : "Download";
}

function SubmitButton({ form }: { form: DownloadForm }) {
  return (
    <Button
      type="submit"
      size="lg"
      className="h-10 w-full sm:w-auto"
      disabled={!form.media || form.createJob.isPending}
    >
      {submitLabel(form)}
    </Button>
  );
}

function LinkField({ form }: { form: DownloadForm }) {
  return (
    <FormField
      label="Link"
      type="url"
      inputMode="url"
      placeholder="https://www.youtube.com/watch?v=…"
      hint="A video, playlist or channel from any site yt-dlp supports."
      required
      value={form.url}
      error={form.check.status === "invalid" ? form.check.message : undefined}
      onPaste={form.markPaste}
      onChange={(event) => form.setUrl(event.target.value)}
    />
  );
}

export function DownloadPage() {
  const form = useDownloadForm();
  const cookieFiles = useCookieFiles().data ?? [];
  const proxyCount = useProxies().data?.length ?? 0;

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    form.submit();
  }

  return (
    <>
      <PageHeader title="Download" />
      <SystemWarnings />
      <form className="space-y-6" onSubmit={handleSubmit} noValidate>
        <FormError message={form.createJob.isError ? describeError(form.createJob.error) : null} />
        <LinkField form={form} />
        <MediaPreview check={form.check} />
        <PlaylistChoice
          videoInPlaylist={form.videoInPlaylist}
          media={form.media}
          wholePlaylist={form.wholePlaylist}
          onWholePlaylistChange={form.setWholePlaylist}
        />
        <PresetField choice={form.presetChoice} />
        <RecordingChoice recording={form.recording} />
        <DownloadSettingsFields
          key={form.settingsVersion}
          value={form.settings}
          onChange={form.setSettings}
          cookieFiles={cookieFiles}
          proxyCount={proxyCount}
        />
        <SubmitButton form={form} />
      </form>
    </>
  );
}
