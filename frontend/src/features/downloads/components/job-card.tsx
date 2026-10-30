import { Progress } from "@/components/ui/progress";
import { JobActions } from "@/features/downloads/components/job-actions";
import { JobStatusBadge } from "@/features/downloads/components/job-status-badge";
import { describeProgress, formatStartTime } from "@/features/downloads/format";
import type { Job } from "@/features/downloads/types";

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
    return <p className="text-xs text-muted-foreground">{describeProgress(job)}</p>;
  }
  if (job.status === "queued") {
    return <p className="text-sm text-muted-foreground">Waiting for a free recording slot…</p>;
  }
  return <JobOutcome job={job} />;
}

function JobOutcome({ job }: { job: Job }) {
  if (job.status === "failed" && job.error) {
    return <p className="text-sm break-words text-destructive">{job.error}</p>;
  }
  if (job.status === "completed" && job.filepath) {
    return <p className="text-xs break-all text-muted-foreground">Saved to {job.filepath}</p>;
  }
  return null;
}

function JobDetails({ job }: { job: Job }) {
  if (job.kind === "live") {
    return <RecordingDetails job={job} />;
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

function JobCard({ job }: { job: Job }) {
  return (
    <li className="space-y-3 rounded-xl border p-4">
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1 space-y-1">
          <p className="truncate font-medium">{job.title ?? job.url}</p>
          {job.title && <p className="truncate text-xs text-muted-foreground">{job.url}</p>}
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
