import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { JobList, formatBytes, useSubscriptionJobs } from "@/features/downloads";
import { useSubscriptionUsage } from "@/features/subscriptions/api";
import type { Subscription } from "@/features/subscriptions/types";

function DownloadRows({ subscription }: { subscription: Subscription }) {
  const jobs = useSubscriptionJobs(subscription.id);
  if (jobs.isPending) {
    return <p className="text-sm text-muted-foreground">Loading downloads…</p>;
  }
  if (jobs.isError) {
    return <FormError message={describeError(jobs.error)} />;
  }
  if (jobs.data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Nothing downloaded or recorded from this channel yet.
      </p>
    );
  }
  return <JobList jobs={jobs.data} label={`Downloads from ${subscription.name}`} />;
}

function UsageLine({ subscription, version }: { subscription: Subscription; version: string }) {
  const usage = useSubscriptionUsage(subscription.id, version).data;
  if (!usage || usage.downloads === 0) {
    return null;
  }
  const downloads = usage.downloads === 1 ? "1 download" : `${usage.downloads} downloads`;
  const files = usage.files === 1 ? "1 file" : `${usage.files} files`;
  return (
    <p className="text-xs text-muted-foreground">
      {downloads} · {files} on disk · {formatBytes(usage.bytes)}
    </p>
  );
}

/** Everything this subscription downloaded or recorded, with the queue's actions. */
export function SubscriptionDownloads({
  subscription,
  id,
}: {
  subscription: Subscription;
  id: string;
}) {
  // Disk usage is fetched again whenever a download finishes or is removed.
  const jobs = useSubscriptionJobs(subscription.id).data ?? [];
  const version = jobs.map((job) => `${job.id}:${job.status}`).join(",");
  return (
    <section id={id} className="space-y-3 border-t pt-3" aria-label="Downloads and recordings">
      <div className="space-y-0.5">
        <h3 className="text-sm font-medium">Downloads and recordings</h3>
        <UsageLine subscription={subscription} version={version} />
      </div>
      <DownloadRows subscription={subscription} />
    </section>
  );
}
