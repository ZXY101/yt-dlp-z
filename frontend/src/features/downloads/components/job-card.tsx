import { Progress } from "@/components/ui/progress";
import { JobActions } from "@/features/downloads/components/job-actions";
import { JobStatusBadge } from "@/features/downloads/components/job-status-badge";
import { describeProgress, formatStartTime } from "@/features/downloads/format";
import type { Job } from "@/features/downloads/types";
import { useProxies } from "@/features/proxies";

function RecordingDetails({ job }: { job: Job }) {
  if (job.status === "scheduled" && job.scheduled_at) {
    return (
      <p className="text-sm text-muted-foreground">
        Stream starts {formatStartTime(job.scheduled_at)}. Recording begins a few minutes before.
      </p>
    );
  }
  if (job.status === "running") {
    // A live stream has no total size, so there is no progress bar.
    const part = recordingPart(job);
    const progress = describeProgress(job);
    return (
      <p className="text-xs text-muted-foreground">{part ? `${part} · ${progress}` : progress}</p>
    );
  }
  if (job.status === "queued") {
    return <p className="text-sm text-muted-foreground">Waiting for a free recording slot…</p>;
  }
  return <JobOutcome job={job} />;
}

/** "Part 2" for recordings split into several files, or continued after a restart. */
function recordingPart(job: Job) {
  const numbered = job.part_seconds !== null || (job.part ?? 0) > 1;
  return numbered && job.part ? `Part ${job.part}` : null;
}

function JobOutcome({ job }: { job: Job }) {
  if (job.status === "failed" && job.error) {
    return <p className="text-sm break-words text-destructive">{job.error}</p>;
  }
  // A stopped recording keeps what it recorded.
  const saved = job.status === "completed" || job.status === "cancelled";
  if (saved && job.filepath) {
    return <p className="text-xs break-all text-muted-foreground">Saved to {job.filepath}</p>;
  }
  return null;
}

function JobDetails({ job }: { job: Job }) {
  if (job.kind === "live") {
    return <RecordingDetails job={job} />;
  }
  if (job.status === "scheduled" && job.scheduled_at) {
    return (
      <p className="text-sm text-muted-foreground">
        Downloads {formatStartTime(job.scheduled_at)}, once YouTube has processed the stream.
      </p>
    );
  }
  if (job.status === "running") {
    return (
      <div className="space-y-1.5">
        <Progress value={job.progress ?? 0} aria-label="Download progress" />
        <p className="text-xs text-muted-foreground">{describeProgress(job)}</p>
      </div>
    );
  }
  if (job.status === "queued") {
    return <p className="text-sm text-muted-foreground">Waiting for a free download slot…</p>;
  }
  return <JobOutcome job={job} />;
}

const SECONDS_PER_HOUR = 3600;

/** A recording's VOD, or the VOD a recording will get. */
function vodNote(job: Job) {
  if (job.source_job_id !== null) {
    return job.vod_replace ? "VOD of a recording · replaces it once saved" : "VOD of a recording";
  }
  if (job.kind === "live" && job.vod_after_seconds) {
    const hours = Math.round(job.vod_after_seconds / SECONDS_PER_HOUR);
    return `VOD downloaded ${hours} h after the stream`;
  }
  return null;
}

/** Which proxy of the pool the download went through. */
function ProxyNote({ proxyId }: { proxyId: number }) {
  const proxies = useProxies().data;
  if (!proxies) {
    return null;
  }
  const proxy = proxies.find((item) => item.id === proxyId);
  return (
    <p className="truncate text-xs text-muted-foreground">
      {proxy ? `Through proxy ${proxy.name}` : "Through a deleted proxy"}
    </p>
  );
}

function JobCard({ job }: { job: Job }) {
  return (
    <li className="space-y-3 rounded-xl border p-4">
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1 space-y-1">
          <p className="truncate font-medium">{job.title ?? job.url}</p>
          {job.title && <p className="truncate text-xs text-muted-foreground">{job.url}</p>}
          {job.proxy_id !== null && <ProxyNote proxyId={job.proxy_id} />}
          {vodNote(job) && <p className="text-xs text-muted-foreground">{vodNote(job)}</p>}
        </div>
        <JobStatusBadge job={job} />
      </div>
      <JobDetails job={job} />
      <JobActions job={job} />
    </li>
  );
}

export function JobList({ jobs, label }: { jobs: Job[]; label: string }) {
  return (
    <ul className="space-y-3" aria-label={label}>
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} />
      ))}
    </ul>
  );
}
