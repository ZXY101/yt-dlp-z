import type { QueryClient } from "@tanstack/react-query";

import type { Job, JobEvent } from "@/features/downloads/types";

export const JOBS_KEY = ["jobs"] as const;

export function isActiveJob(job: Job) {
  return job.status === "queued" || job.status === "running";
}

/** Inserts or replaces a job, keeping the list newest first. Leaves an unloaded list alone. */
export function upsertJob(jobs: Job[] | undefined, job: Job): Job[] | undefined {
  if (!jobs) {
    return jobs;
  }
  const others = jobs.filter((existing) => existing.id !== job.id);
  return [...others, job].toSorted((a, b) => b.id - a.id);
}

export function removeJob(jobs: Job[] | undefined, jobId: number): Job[] | undefined {
  return jobs?.filter((job) => job.id !== jobId);
}

export function applyJobEvent(queryClient: QueryClient, event: JobEvent) {
  if (event.type === "job") {
    queryClient.setQueryData<Job[]>(JOBS_KEY, (jobs) => upsertJob(jobs, event.job));
    return;
  }
  queryClient.setQueryData<Job[]>(JOBS_KEY, (jobs) => removeJob(jobs, event.id));
}
