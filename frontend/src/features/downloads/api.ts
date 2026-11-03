import { skipToken, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";
import { JOBS_KEY, forgetJob, saveJob, subscriptionJobsKey } from "@/features/downloads/jobs";
import type { Job, JobCreate, MediaProbeRequest } from "@/features/downloads/types";

const LOG_REFRESH_MS = 2000;
// A link's answer rarely changes while the form is open; re-checking costs a yt-dlp run.
const PROBE_STALE_MS = 5 * 60_000;

function jobPath(jobId: number) {
  return { params: { path: { job_id: jobId } } };
}

export function useJobs() {
  return useQuery({ queryKey: JOBS_KEY, queryFn: () => unwrap(api.GET("/api/jobs")) });
}

/** Everything one channel subscription queued, newest first. Kept live by job events. */
export function useSubscriptionJobs(subscriptionId: number) {
  return useQuery({
    queryKey: subscriptionJobsKey(subscriptionId),
    queryFn: () =>
      unwrap(
        api.GET("/api/jobs", {
          params: { query: { subscription_id: subscriptionId, limit: 1000 } },
        }),
      ),
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: JobCreate) => unwrap(api.POST("/api/jobs", { body })),
    onSuccess: (job) => saveJob(queryClient, job),
  });
}

/** Asks yt-dlp what a link is. `null` checks nothing. */
export function useMediaProbe(request: MediaProbeRequest | null) {
  return useQuery({
    queryKey: ["media-probe", request],
    queryFn: request ? () => unwrap(api.POST("/api/media/probe", { body: request })) : skipToken,
    staleTime: PROBE_STALE_MS,
    // A failed check is yt-dlp's answer (bad link, private video); retrying won't change it.
    retry: false,
  });
}

/** Cancel and retry return the updated job. The WebSocket also delivers it, but
 * applying it here keeps the UI right even while the socket is reconnecting. */
function useJobUpdate(send: (jobId: number) => Promise<Job>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: send,
    onSuccess: (job) => saveJob(queryClient, job),
  });
}

export function useCancelJob() {
  return useJobUpdate((jobId) => unwrap(api.POST("/api/jobs/{job_id}/cancel", jobPath(jobId))));
}

export function useRetryJob() {
  return useJobUpdate((jobId) => unwrap(api.POST("/api/jobs/{job_id}/retry", jobPath(jobId))));
}

export function useDeleteJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: number) => unwrap(api.DELETE("/api/jobs/{job_id}", jobPath(jobId))),
    onSuccess: (_data, jobId) => forgetJob(queryClient, jobId),
  });
}

export function useJobLog(job: Job, enabled: boolean) {
  return useQuery({
    queryKey: ["jobs", job.id, "log"],
    queryFn: () =>
      unwrap(api.GET("/api/jobs/{job_id}/log", { ...jobPath(job.id), parseAs: "text" })),
    enabled,
    refetchInterval: job.status === "running" ? LOG_REFRESH_MS : false,
  });
}
