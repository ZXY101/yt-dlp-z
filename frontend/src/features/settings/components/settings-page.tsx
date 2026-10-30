import { useState } from "react";

import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { PageHeader } from "@/components/page-header";
import { SuccessMessage } from "@/components/success-message";
import { Button } from "@/components/ui/button";
import { useAppSettings, useSaveAppSettings } from "@/features/settings/api";
import type { AppSettings } from "@/features/settings/types";

const MAX_DOWNLOADS = 10;

function validateLimit(text: string) {
  const limit = Number(text);
  if (!Number.isInteger(limit) || limit < 1 || limit > MAX_DOWNLOADS) {
    return `Enter a whole number from 1 to ${MAX_DOWNLOADS}.`;
  }
  return undefined;
}

function SettingsForm({ settings }: { settings: AppSettings }) {
  const [downloadDir, setDownloadDir] = useState(settings.download_dir);
  const [limit, setLimit] = useState(String(settings.max_concurrent_downloads));
  const [limitError, setLimitError] = useState<string>();
  const save = useSaveAppSettings();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const error = validateLimit(limit);
    setLimitError(error);
    if (!error) {
      save.mutate({
        ...settings,
        download_dir: downloadDir.trim(),
        max_concurrent_downloads: Number(limit),
      });
    }
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit} noValidate>
      <FormError message={save.isError ? describeError(save.error) : null} />
      {save.isSuccess && <SuccessMessage>Settings saved.</SuccessMessage>}
      <FormField
        label="Download folder"
        hint="Absolute path on the server. Applies to downloads started from now on."
        spellCheck={false}
        value={downloadDir}
        onChange={(event) => setDownloadDir(event.target.value)}
      />
      <FormField
        label="Downloads at the same time"
        inputMode="numeric"
        hint="More parallel downloads finish a queue faster but make rate limits more likely."
        value={limit}
        error={limitError}
        onChange={(event) => setLimit(event.target.value)}
      />
      <Button type="submit" size="lg" className="h-10" disabled={save.isPending}>
        {save.isPending ? "Saving…" : "Save settings"}
      </Button>
    </form>
  );
}

export function SettingsPage() {
  const settings = useAppSettings();
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader title="Settings" />
      {settings.isPending && <p className="text-sm text-muted-foreground">Loading settings…</p>}
      {settings.isError && <FormError message={describeError(settings.error)} />}
      {settings.data && <SettingsForm settings={settings.data} />}
    </div>
  );
}
