import { Badge } from "@/components/ui/badge";
import type { JobStatus } from "@/features/downloads/types";

const STATUS_DISPLAY: Record<
  JobStatus,
  { label: string; variant: React.ComponentProps<typeof Badge>["variant"] }
> = {
  queued: { label: "Queued", variant: "secondary" },
  running: { label: "Downloading", variant: "default" },
  completed: { label: "Done", variant: "outline" },
  failed: { label: "Failed", variant: "destructive" },
  cancelled: { label: "Cancelled", variant: "outline" },
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  const { label, variant } = STATUS_DISPLAY[status];
  return (
    <Badge variant={variant} className="shrink-0">
      {label}
    </Badge>
  );
}
