import { FormError } from "@/components/form-error";
import { SuccessMessage } from "@/components/success-message";
import type { YtdlpInfo } from "@/features/settings/types";

function formatCheckTime(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function LatestText({ info }: { info: YtdlpInfo }) {
  if (!info.latest_version || !info.checked_at) {
    return null;
  }
  if (info.latest_version !== info.active_version) {
    return <p className="text-sm font-medium">yt-dlp {info.latest_version} is available.</p>;
  }
  return (
    <p className="text-sm text-muted-foreground">
      The newest version (checked {formatCheckTime(info.checked_at)}).
    </p>
  );
}

/** Which yt-dlp runs, and whether a newer one was found. */
export function VersionStatus({ info }: { info: YtdlpInfo }) {
  const origin = info.using_update
    ? `updated (the app came with ${info.bundled_version})`
    : "bundled with the app";
  return (
    <div className="space-y-1">
      <p className="text-sm">
        Version {info.active_version}, {origin}.
      </p>
      <LatestText info={info} />
    </div>
  );
}

/** How the last update since the app started went. */
export function UpdateResult({ info }: { info: YtdlpInfo }) {
  const { state, message } = info.update;
  if (state === "succeeded" && message) {
    return <SuccessMessage>{message}</SuccessMessage>;
  }
  return <FormError message={state === "failed" ? (message ?? null) : null} />;
}
