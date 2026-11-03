import type { QueryClient } from "@tanstack/react-query";

import type { Job, JobEvent } from "@/features/downloads/types";

export const JOBS_KEY = ["jobs"] as const;
// What one channel subscription queued, shown on the Subscriptions page.
const SUBSCRIPTION_JOBS_KEY = ["jobs", "subscription"] as const;

export function subscriptionJobsKey(subscriptionId: number) {
  return [...SUBSCRIPTION_JOBS_KEY, subscriptionId] as const;
}

export function isActiveJob(job: Job) {
  return job.status === "queued" || job.status === "running";
}

export function isFinishedJob(job: Job) {
  return job.status === "completed" || job.status === "failed" || job.status === "cancelled";
}

/** Scheduled recordings, the soonest first. */
export function scheduledJobs(jobs: Job[]) {
  const scheduled = jobs.filter((job) => job.status === "scheduled");
  return scheduled.toSorted((a, b) => (a.scheduled_at ?? "").localeCompare(b.scheduled_at ?? ""));
}

/** Inserts or replaces a job, keeping the list newest first. Leaves an unloaded list alone.
 * HTTP responses and WebSocket events can arrive out of order, so an update older than
 * the cached copy (lower revision) is ignored. */
export function upsertJob(jobs: Job[] | undefined, job: Job): Job[] | undefined {
  if (!jobs) {
    return jobs;
  }
  const cached = jobs.find((existing) => existing.id === job.id);
  if (cached && cached.revision > job.revision) {
    return jobs;
  }
  const others = jobs.filter((existing) => existing.id !== job.id);
  return [...others, job].toSorted((a, b) => b.id - a.id);
}

export function removeJob(jobs: Job[] | undefined, jobId: number): Job[] | undefined {
  return jobs?.filter((job) => job.id !== jobId);
}

/** The queue's list and each subscription's list hold the same jobs; keeps them in step. */
export function saveJob(queryClient: QueryClient, job: Job) {
  queryClient.setQueryData<Job[]>(JOBS_KEY, (jobs) => upsertJob(jobs, job));
  if (job.subscription_id !== null) {
    const key = subscriptionJobsKey(job.subscription_id);
    queryClient.setQueryData<Job[]>(key, (jobs) => upsertJob(jobs, job));
  }
}

export function forgetJob(queryClient: QueryClient, jobId: number) {
  queryClient.setQueryData<Job[]>(JOBS_KEY, (jobs) => removeJob(jobs, jobId));
  queryClient.setQueriesData<Job[]>({ queryKey: SUBSCRIPTION_JOBS_KEY }, (jobs) =>
    removeJob(jobs, jobId),
  );
}

export function applyJobEvent(queryClient: QueryClient, event: JobEvent) {
  if (event.type === "job") {
    saveJob(queryClient, event.job);
    return;
  }
  forgetJob(queryClient, event.id);
}
