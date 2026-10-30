import { FileText, type LucideIcon, RotateCcw, Square, Trash2 } from "lucide-react";
import { useState } from "react";

import { describeError } from "@/api/errors";
import { Button } from "@/components/ui/button";
import { useCancelJob, useDeleteJob, useRetryJob } from "@/features/downloads/api";
import { JobLogDialog } from "@/features/downloads/components/job-log-dialog";
import { isFinishedJob } from "@/features/downloads/jobs";
import type { Job } from "@/features/downloads/types";

interface ActionButtonProps {
  icon: LucideIcon;
  text: string;
  /** Full accessible name, since every card has the same visible button text. */
  label?: string;
  variant?: "ghost" | "outline";
  disabled?: boolean;
  onClick: () => void;
}

function ActionButton({ icon: Icon, text, label, variant = "ghost", ...props }: ActionButtonProps) {
  return (
    <Button variant={variant} className="h-10" aria-label={label} {...props}>
      <Icon aria-hidden />
      {text}
    </Button>
  );
}

function useJobMutations() {
  const cancel = useCancelJob();
  const retry = useRetryJob();
  const remove = useDeleteJob();
  const failed = [cancel, retry, remove].find((mutation) => mutation.isError);
  return { cancel, retry, remove, error: failed ? describeError(failed.error) : null };
}

export function JobActions({ job }: { job: Job }) {
  const [logOpen, setLogOpen] = useState(false);
  const { cancel, retry, remove, error } = useJobMutations();
  const finished = isFinishedJob(job);
  const canRetry = job.status === "failed" || job.status === "cancelled";
  const name = job.title ?? job.url;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap justify-end gap-2">
        <ActionButton icon={FileText} text="Log" onClick={() => setLogOpen(true)} />
        {!finished && (
          <ActionButton
            icon={Square}
            text="Cancel"
            label={`Cancel ${name}`}
            variant="outline"
            disabled={cancel.isPending}
            onClick={() => cancel.mutate(job.id)}
          />
        )}
        {canRetry && (
          <ActionButton
            icon={RotateCcw}
            text="Retry"
            label={`Retry ${name}`}
            variant="outline"
            disabled={retry.isPending}
            onClick={() => retry.mutate(job.id)}
          />
        )}
        {finished && (
          <ActionButton
            icon={Trash2}
            text="Remove"
            label={`Remove ${name} from the list`}
            disabled={remove.isPending}
            onClick={() => remove.mutate(job.id)}
          />
        )}
      </div>
      {error && <p className="text-right text-sm text-destructive">{error}</p>}
      <JobLogDialog job={job} open={logOpen} onOpenChange={setLogOpen} />
    </div>
  );
}
