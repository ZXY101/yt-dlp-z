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
import {
  LiveStreamFields,
  useLiveStreamFields,
} from "@/features/settings/components/live-stream-fields";
import { type LimitField, useLimitField } from "@/features/settings/hooks/use-limit-field";
import type { AppSettings } from "@/features/settings/types";

const MAX_DOWNLOADS = 10;
const MAX_CHANNELS = 100;
// Above this many channels, polling from one IP risks YouTube rate limits.
const SAFE_CHANNELS = 5;

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

function DownloadLimitField({ field }: { field: LimitField }) {
  return (
    <FormField
      label="Downloads at the same time"
      inputMode="numeric"
      hint="More parallel downloads finish a queue faster but make rate limits more likely."
      value={field.value}
      error={field.error}
      onChange={(event) => field.setValue(event.target.value)}
    />
  );
}

function SettingsForm({ settings }: { settings: AppSettings }) {
  const [downloadDir, setDownloadDir] = useState(settings.download_dir);
  const downloads = useLimitField(settings.max_concurrent_downloads, { max: MAX_DOWNLOADS });
  const recordings = useLimitField(settings.max_concurrent_recordings, { max: MAX_DOWNLOADS });
  const channels = useLimitField(settings.max_subscriptions, { max: MAX_CHANNELS });
  const recording = useLiveStreamFields(settings.recording);
  const save = useSaveAppSettings();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // Every field is checked, so all errors show at once.
    const valid = [downloads.check(), recordings.check(), channels.check(), recording.check()];
    if (valid.every(Boolean)) {
      save.mutate({
        download_dir: downloadDir.trim(),
        max_concurrent_downloads: Number(downloads.value),
        max_concurrent_recordings: Number(recordings.value),
        max_subscriptions: Number(channels.value),
        recording: recording.values(),
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
      <DownloadLimitField field={downloads} />
      <ChannelLimitField
        value={channels.value}
        error={channels.error}
        onChange={channels.setValue}
      />
      <LiveStreamFields recording={recording} concurrent={recordings} />
      <Button type="submit" size="lg" className="h-10" disabled={save.isPending}>
        {save.isPending ? "Saving…" : "Save settings"}
      </Button>
    </form>
  );
}

export function SettingsPage() {
  const settings = useAppSettings();
  return (
    <>
      <PageHeader title="Settings" />
      {settings.isPending && <p className="text-sm text-muted-foreground">Loading settings…</p>}
      {settings.isError && <FormError message={describeError(settings.error)} />}
      {settings.data && <SettingsForm settings={settings.data} />}
    </>
  );
}
