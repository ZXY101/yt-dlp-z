import { FileText, type LucideIcon, Pin, PinOff, RotateCcw, Square } from "lucide-react";
import { useState } from "react";

import { describeError } from "@/api/errors";
import { Button } from "@/components/ui/button";
import { useCancelJob, useDeleteJob, useRetryJob, useSetJobKeep } from "@/features/downloads/api";
import { JobLogDialog } from "@/features/downloads/components/job-log-dialog";
import { RemoveJobButton } from "@/features/downloads/components/remove-job-button";
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
  const keep = useSetJobKeep();
  const failed = [cancel, retry, remove, keep].find((mutation) => mutation.isError);
  return { cancel, retry, remove, keep, error: failed ? describeError(failed.error) : null };
}

/** Subscription downloads can be pinned against "delete after N days". */
function KeepButton({ job, mutation }: { job: Job; mutation: ReturnType<typeof useSetJobKeep> }) {
  const name = job.title ?? job.url;
  return (
    <Button
      variant={job.keep ? "outline" : "ghost"}
      className="h-10"
      aria-label={job.keep ? `Stop keeping ${name}` : `Keep ${name}`}
      aria-pressed={job.keep}
      disabled={mutation.isPending}
      onClick={() => mutation.mutate({ jobId: job.id, keep: !job.keep })}
    >
      {job.keep ? <PinOff aria-hidden /> : <Pin aria-hidden />}
      {job.keep ? "Kept" : "Keep"}
    </Button>
  );
}

export function JobActions({ job }: { job: Job }) {
  const [logOpen, setLogOpen] = useState(false);
  const { cancel, retry, remove, keep, error } = useJobMutations();
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
        {finished && job.subscription_id !== null && <KeepButton job={job} mutation={keep} />}
        {finished && (
          <RemoveJobButton
            job={job}
            disabled={remove.isPending}
            onRemove={(deleteFiles) => remove.mutate({ jobId: job.id, deleteFiles })}
          />
        )}
      </div>
      {error && <p className="text-right text-sm text-destructive">{error}</p>}
      <JobLogDialog job={job} open={logOpen} onOpenChange={setLogOpen} />
    </div>
  );
}
