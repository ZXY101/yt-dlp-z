import type { UseQueryResult } from "@tanstack/react-query";

import { describeError } from "@/api/errors";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useJobLog } from "@/features/downloads/api";
import type { Job } from "@/features/downloads/types";

interface JobLogDialogProps {
  job: Job;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function logText(log: UseQueryResult<string>) {
  if (log.isPending) {
    return "Loading…";
  }
  if (log.isError) {
    return describeError(log.error);
  }
  return log.data || "Nothing logged yet.";
}

export function JobLogDialog({ job, open, onOpenChange }: JobLogDialogProps) {
  const log = useJobLog(job, open);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Download log</DialogTitle>
          <DialogDescription className="truncate">{job.title ?? job.url}</DialogDescription>
        </DialogHeader>
        <pre className="max-h-[60vh] overflow-auto rounded-lg bg-muted p-3 text-xs break-all whitespace-pre-wrap">
          {logText(log)}
        </pre>
      </DialogContent>
    </Dialog>
  );
}
