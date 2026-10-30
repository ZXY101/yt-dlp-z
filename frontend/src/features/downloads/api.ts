import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";
import { JOBS_KEY, removeJob, upsertJob } from "@/features/downloads/jobs";
import type { Job, JobCreate } from "@/features/downloads/types";

const LOG_REFRESH_MS = 2000;

function jobPath(jobId: number) {
  return { params: { path: { job_id: jobId } } };
}

export function useJobs() {
  return useQuery({ queryKey: JOBS_KEY, queryFn: () => unwrap(api.GET("/api/jobs")) });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: JobCreate) => unwrap(api.POST("/api/jobs", { body })),
    onSuccess: (job) => queryClient.setQueryData<Job[]>(JOBS_KEY, (jobs) => upsertJob(jobs, job)),
  });
}

/** Cancel and retry return the updated job. The WebSocket also delivers it, but
 * applying it here keeps the UI right even while the socket is reconnecting. */
function useJobUpdate(send: (jobId: number) => Promise<Job>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: send,
    onSuccess: (job) => queryClient.setQueryData<Job[]>(JOBS_KEY, (jobs) => upsertJob(jobs, job)),
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
    onSuccess: (_data, jobId) =>
      queryClient.setQueryData<Job[]>(JOBS_KEY, (jobs) => removeJob(jobs, jobId)),
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
