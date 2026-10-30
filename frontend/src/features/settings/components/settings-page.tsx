import { TriangleAlert } from "lucide-react";
import { useState } from "react";

import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { PageHeader } from "@/components/page-header";
import { SuccessMessage } from "@/components/success-message";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useAppSettings, useSaveAppSettings } from "@/features/settings/api";
import type { AppSettings } from "@/features/settings/types";

const MAX_DOWNLOADS = 10;
const MAX_CHANNELS = 100;
// Above this many channels, polling from one IP risks YouTube rate limits.
const SAFE_CHANNELS = 5;

function validateLimit(text: string, max: number) {
  const limit = Number(text);
  if (!Number.isInteger(limit) || limit < 1 || limit > max) {
    return `Enter a whole number from 1 to ${max}.`;
  }
  return undefined;
}

/** A whole-number field from 1 to `max`; `check()` shows its error and says if it's valid. */
function useLimitField(initial: number, max: number) {
  const [value, setValue] = useState(String(initial));
  const [error, setError] = useState<string>();

  function check() {
    const problem = validateLimit(value, max);
    setError(problem);
    return problem === undefined;
  }

  return { value, setValue, error, check };
}

interface ChannelLimitFieldProps {
  value: string;
  error: string | undefined;
  onChange: (value: string) => void;
}

function ChannelLimitField({ value, error, onChange }: ChannelLimitFieldProps) {
  return (
    <>
      <FormField
        label="Channels to watch"
        inputMode="numeric"
        hint="The most subscriptions allowed, paused ones included."
        value={value}
        error={error}
        onChange={(event) => onChange(event.target.value)}
      />
      {Number(value) > SAFE_CHANNELS && <ChannelLimitWarning />}
    </>
  );
}

function ChannelLimitWarning() {
  return (
    <Alert>
      <TriangleAlert aria-hidden />
      <AlertDescription>
        Watching more than {SAFE_CHANNELS} channels from one IP address can get it rate-limited or
        flagged by YouTube. Use longer check intervals, or a proxy, when watching many channels.
      </AlertDescription>
    </Alert>
  );
}

type LimitField = ReturnType<typeof useLimitField>;

function ConcurrencyFields({
  downloads,
  recordings,
}: {
  downloads: LimitField;
  recordings: LimitField;
}) {
  return (
    <>
      <FormField
        label="Downloads at the same time"
        inputMode="numeric"
        hint="More parallel downloads finish a queue faster but make rate limits more likely."
        value={downloads.value}
        error={downloads.error}
        onChange={(event) => downloads.setValue(event.target.value)}
      />
      <FormField
        label="Recordings at the same time"
        inputMode="numeric"
        hint="Live streams being recorded. Counted apart from downloads, so they never wait behind them."
        value={recordings.value}
        error={recordings.error}
        onChange={(event) => recordings.setValue(event.target.value)}
      />
    </>
  );
}

function SettingsForm({ settings }: { settings: AppSettings }) {
  const [downloadDir, setDownloadDir] = useState(settings.download_dir);
  const downloads = useLimitField(settings.max_concurrent_downloads, MAX_DOWNLOADS);
  const recordings = useLimitField(settings.max_concurrent_recordings, MAX_DOWNLOADS);
  const channels = useLimitField(settings.max_subscriptions, MAX_CHANNELS);
  const save = useSaveAppSettings();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // Every field is checked, so all errors show at once.
    const valid = [downloads.check(), recordings.check(), channels.check()];
    if (valid.every(Boolean)) {
      save.mutate({
        download_dir: downloadDir.trim(),
        max_concurrent_downloads: Number(downloads.value),
        max_concurrent_recordings: Number(recordings.value),
        max_subscriptions: Number(channels.value),
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
      <ConcurrencyFields downloads={downloads} recordings={recordings} />
      <ChannelLimitField
        value={channels.value}
        error={channels.error}
        onChange={channels.setValue}
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
