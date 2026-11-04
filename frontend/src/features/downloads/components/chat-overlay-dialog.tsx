import { useState } from "react";

import { describeError } from "@/api/errors";
import { OverlayStyleFields } from "@/components/download-options/overlay-style-fields";
import { FormError } from "@/components/form-error";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useRebuildChatOverlay } from "@/features/downloads/api";
import type { Job } from "@/features/downloads/types";
import { overlayStyleOf } from "@/lib/live-chat";

interface ChatOverlayDialogProps {
  job: Job;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function OverlayForm({ job, onDone }: { job: Job; onDone: () => void }) {
  const [style, setStyle] = useState(() => overlayStyleOf(job.live_chat));
  const rebuild = useRebuildChatOverlay();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    rebuild.mutate({ jobId: job.id, style }, { onSuccess: onDone });
  }

  return (
    <form className="max-h-[70vh] space-y-4 overflow-y-auto pr-1" onSubmit={handleSubmit}>
      <FormError message={rebuild.isError ? describeError(rebuild.error) : null} />
      <OverlayStyleFields value={style} onChange={setStyle} />
      <Button type="submit" className="h-10" disabled={rebuild.isPending}>
        {rebuild.isPending ? "Building…" : "Rebuild overlay"}
      </Button>
    </form>
  );
}

/** Builds the overlay again from the saved chat; the video isn't touched. */
export function ChatOverlayDialog({ job, open, onOpenChange }: ChatOverlayDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Chat overlay</DialogTitle>
          <DialogDescription>
            Replaces the overlay using the saved chat. A player that has the video open may need
            reopening to show it.
          </DialogDescription>
        </DialogHeader>
        {open && <OverlayForm job={job} onDone={() => onOpenChange(false)} />}
      </DialogContent>
    </Dialog>
  );
}
