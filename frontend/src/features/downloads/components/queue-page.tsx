import type { UseQueryResult } from "@tanstack/react-query";
import { ListVideo } from "lucide-react";

import { describeError } from "@/api/errors";
import { EmptyState } from "@/components/empty-state";
import { FormError } from "@/components/form-error";
import { PageHeader } from "@/components/page-header";
import { useJobs } from "@/features/downloads/api";
import { JobList } from "@/features/downloads/components/job-card";
import { NewDownloadButton } from "@/features/downloads/components/new-download-button";
import { isActiveJob } from "@/features/downloads/jobs";
import type { Job } from "@/features/downloads/types";

function JobSection({ title, jobs }: { title: string; jobs: Job[] }) {
  if (jobs.length === 0) {
    return null;
  }
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-medium">{title}</h2>
      <JobList jobs={jobs} label={title} />
    </section>
  );
}

function QueueContent({ jobs }: { jobs: UseQueryResult<Job[]> }) {
  if (jobs.isPending) {
    return <p className="text-sm text-muted-foreground">Loading downloads…</p>;
  }
  if (jobs.isError) {
    return <FormError message={describeError(jobs.error)} />;
  }
  if (jobs.data.length === 0) {
    return (
      <EmptyState
        icon={ListVideo}
        title="No downloads yet"
        description="Downloads you start show up here with their progress."
      />
    );
  }
  return (
    <div className="space-y-8">
      <JobSection title="In progress" jobs={jobs.data.filter(isActiveJob)} />
      <JobSection title="Finished" jobs={jobs.data.filter((job) => !isActiveJob(job))} />
    </div>
  );
}

export function QueuePage() {
  const jobs = useJobs();
  return (
    <div className="space-y-6">
      <PageHeader title="Queue" action={<NewDownloadButton />} />
      <QueueContent jobs={jobs} />
    </div>
  );
}
