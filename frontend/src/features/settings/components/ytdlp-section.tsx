import { RefreshCw, Search } from "lucide-react";

import { describeError } from "@/api/errors";
import { CheckboxField } from "@/components/checkbox-field";
import { FormError } from "@/components/form-error";
import { SelectField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import { UpdateResult, VersionStatus } from "@/features/settings/components/ytdlp-status";
import type { YtdlpChannel, YtdlpInfo } from "@/features/settings/types";
import {
  useCheckYtdlp,
  useRefreshOnVersionChange,
  useRemoveYtdlpUpdate,
  useSaveYtdlpPreferences,
  useStartYtdlpUpdate,
  useYtdlpInfo,
} from "@/features/settings/ytdlp-api";

const CHANNELS: { value: YtdlpChannel; label: string }[] = [
  { value: "stable", label: "Stable" },
  { value: "nightly", label: "Nightly" },
];

function useYtdlpActions() {
  const check = useCheckYtdlp();
  const update = useStartYtdlpUpdate();
  const remove = useRemoveYtdlpUpdate();
  const failed = [check, update, remove].find((mutation) => mutation.isError);
  return { check, update, remove, error: failed ? describeError(failed.error) : null };
}

function PreferenceFields({ info, busy }: { info: YtdlpInfo; busy: boolean }) {
  const preferences = useSaveYtdlpPreferences();
  const current = { channel: info.channel, auto_update: info.auto_update };
  return (
    <>
      <FormError message={preferences.isError ? describeError(preferences.error) : null} />
      <SelectField
        label="Update channel"
        hint="Nightly gets YouTube fixes sooner but is less tested."
        value={info.channel}
        choices={CHANNELS}
        disabled={busy}
        onValueChange={(channel) => preferences.mutate({ ...current, channel })}
      />
      <CheckboxField
        label="Update automatically"
        description="Checks once a day and installs a newer version when one is out."
        checked={info.auto_update}
        disabled={busy}
        onCheckedChange={(autoUpdate) =>
          preferences.mutate({ ...current, auto_update: autoUpdate })
        }
      />
    </>
  );
}

function YtdlpControls({ info }: { info: YtdlpInfo }) {
  const { check, update, remove, error } = useYtdlpActions();
  const running = info.update.state === "running";

  return (
    <div className="space-y-4">
      <VersionStatus info={info} />
      <FormError message={error} />
      <UpdateResult info={info} />
      <PreferenceFields info={info} busy={running} />
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
        <Button
          type="button"
          variant="outline"
          className="h-10"
          disabled={running || check.isPending}
          onClick={() => check.mutate(undefined)}
        >
          <Search aria-hidden />
          {check.isPending ? "Checking…" : "Check for updates"}
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
