import { Inbox } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { JobList, NewDownloadButton, isActiveJob, useJobs } from "@/features/downloads";
import { SystemWarnings } from "@/features/system";

function ActiveDownloads() {
  const jobs = useJobs();
  const active = (jobs.data ?? []).filter(isActiveJob);
  if (active.length === 0) {
    return (
      <EmptyState
        icon={Inbox}
        title="Nothing downloading right now"
        description="Start a download and its progress shows up here."
      />
    );
  }
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-medium">Active downloads</h2>
      <JobList jobs={active} label="Active downloads" />
    </section>
  );
}

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" action={<NewDownloadButton />} />
      <SystemWarnings />
      <ActiveDownloads />
    </div>
  );
}
