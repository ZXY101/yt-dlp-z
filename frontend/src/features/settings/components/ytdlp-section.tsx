import { RefreshCw } from "lucide-react";

import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { SelectField } from "@/components/form-field";
import { SuccessMessage } from "@/components/success-message";
import { Button } from "@/components/ui/button";
import type { YtdlpChannel, YtdlpInfo } from "@/features/settings/types";
import {
  useRefreshOnVersionChange,
  useRemoveYtdlpUpdate,
  useSetYtdlpChannel,
  useStartYtdlpUpdate,
  useYtdlpInfo,
} from "@/features/settings/ytdlp-api";

const CHANNELS: { value: YtdlpChannel; label: string }[] = [
  { value: "stable", label: "Stable" },
  { value: "nightly", label: "Nightly" },
];

function VersionText({ info }: { info: YtdlpInfo }) {
  if (!info.using_update) {
    return <p className="text-sm">Version {info.active_version}, bundled with the app.</p>;
  }
  return (
    <p className="text-sm">
      Version {info.active_version}, updated (the app came with {info.bundled_version}).
    </p>
  );
}

function UpdateResult({ info }: { info: YtdlpInfo }) {
  const { state, message } = info.update;
  if (state === "succeeded" && message) {
    return <SuccessMessage>{message}</SuccessMessage>;
  }
  return <FormError message={state === "failed" ? (message ?? null) : null} />;
}

function YtdlpControls({ info }: { info: YtdlpInfo }) {
  const setChannel = useSetYtdlpChannel();
  const update = useStartYtdlpUpdate();
  const remove = useRemoveYtdlpUpdate();
  const running = info.update.state === "running";
  const failed = [setChannel, update, remove].find((mutation) => mutation.isError);

  return (
    <div className="space-y-4">
      <VersionText info={info} />
      <FormError message={failed ? describeError(failed.error) : null} />
      <UpdateResult info={info} />
      <SelectField
        label="Update channel"
        hint="Nightly gets YouTube fixes sooner but is less tested."
        value={info.channel}
        choices={CHANNELS}
        disabled={running || setChannel.isPending}
        onValueChange={(channel) => setChannel.mutate(channel)}
      />
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          className="h-10"
          disabled={running || update.isPending}
          onClick={() => update.mutate(undefined)}
        >
          <RefreshCw className={running ? "animate-spin" : undefined} aria-hidden />
          {running ? "Updating…" : "Update now"}
        </Button>
        {info.using_update && (
          <Button
            type="button"
            variant="outline"
            className="h-10"
            disabled={running || remove.isPending}
            onClick={() => remove.mutate(undefined)}
          >
            Use bundled version
          </Button>
        )}
      </div>
    </div>
  );
}

/** Updates yt-dlp without a new app release; YouTube changes often break old versions. */
export function YtdlpSection() {
  const info = useYtdlpInfo();
  useRefreshOnVersionChange(info.data?.active_version);
  return (
    <section className="space-y-4 border-t pt-6" aria-labelledby="ytdlp-heading">
      <div className="space-y-1">
        <h2 id="ytdlp-heading" className="text-lg font-medium">
          yt-dlp
        </h2>
        <p className="text-sm text-muted-foreground">
          Updates apply to downloads started afterwards and are kept across app updates.
        </p>
      </div>
      {info.isError && <FormError message={describeError(info.error)} />}
      {info.data && <YtdlpControls info={info.data} />}
    </section>
  );
}
