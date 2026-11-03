import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { JobList, useSubscriptionJobs } from "@/features/downloads";
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

/** Everything this subscription downloaded or recorded, with the queue's actions. */
export function SubscriptionDownloads({
  subscription,
  id,
}: {
  subscription: Subscription;
  id: string;
}) {
  return (
    <section id={id} className="space-y-3 border-t pt-3" aria-label="Downloads and recordings">
      <h3 className="text-sm font-medium">Downloads and recordings</h3>
      <DownloadRows subscription={subscription} />
    </section>
  );
}
