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

function SettingsForm({ settings }: { settings: AppSettings }) {
  const [downloadDir, setDownloadDir] = useState(settings.download_dir);
  const [limit, setLimit] = useState(String(settings.max_concurrent_downloads));
  const [limitError, setLimitError] = useState<string>();
  const [channels, setChannels] = useState(String(settings.max_subscriptions));
  const [channelsError, setChannelsError] = useState<string>();
  const save = useSaveAppSettings();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const errors = [validateLimit(limit, MAX_DOWNLOADS), validateLimit(channels, MAX_CHANNELS)];
    setLimitError(errors[0]);
    setChannelsError(errors[1]);
    if (errors.every((error) => error === undefined)) {
      save.mutate({
        download_dir: downloadDir.trim(),
        max_concurrent_downloads: Number(limit),
        max_subscriptions: Number(channels),
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
      <ChannelLimitField value={channels} error={channelsError} onChange={setChannels} />
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
