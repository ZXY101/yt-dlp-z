import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { AdvancedOptions } from "@/features/downloads/components/advanced-options";
import { CommonOptions } from "@/features/downloads/components/common-options";
import { useDownloadForm } from "@/features/downloads/hooks/use-download-form";

export function DownloadPage() {
  const form = useDownloadForm();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    form.submit();
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader title="New download" />
      <form className="space-y-6" onSubmit={handleSubmit} noValidate>
        <FormError message={form.createJob.isError ? describeError(form.createJob.error) : null} />
        <FormField
          label="Link"
          type="url"
          inputMode="url"
          placeholder="https://www.youtube.com/watch?v=…"
          hint="A video, playlist or channel from any site yt-dlp supports."
          required
          value={form.fields.url}
          error={form.urlError}
          onChange={(event) => form.setters.setUrl(event.target.value)}
        />
        <FormField
          label="Save to"
          placeholder="Default download folder"
          hint="Leave empty for the default folder. A relative path creates a sub-folder in it."
          value={form.fields.outputDir}
          onChange={(event) => form.setters.setOutputDir(event.target.value)}
        />
        <CommonOptions form={form} />
        <AdvancedOptions form={form} />
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
