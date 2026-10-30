import { Badge } from "@/components/ui/badge";
import type { Job, JobStatus } from "@/features/downloads/types";

type BadgeVariant = React.ComponentProps<typeof Badge>["variant"];

const STATUS_DISPLAY: Record<JobStatus, { label: string; variant: BadgeVariant }> = {
  scheduled: { label: "Scheduled", variant: "secondary" },
  queued: { label: "Queued", variant: "secondary" },
  running: { label: "Downloading", variant: "default" },
  completed: { label: "Done", variant: "outline" },
  failed: { label: "Failed", variant: "destructive" },
  cancelled: { label: "Cancelled", variant: "outline" },
};

function labelFor(job: Job) {
  if (job.kind === "live" && job.status === "running") {
    return "Recording";
  }
  return STATUS_DISPLAY[job.status].label;
}

export function JobStatusBadge({ job }: { job: Job }) {
  return (
    <Badge variant={STATUS_DISPLAY[job.status].variant} className="shrink-0">
      {labelFor(job)}
    </Badge>
  );
}
