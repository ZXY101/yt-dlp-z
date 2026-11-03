import { Trash2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import type { Job } from "@/features/downloads/types";

interface RemoveJobButtonProps {
  job: Job;
  disabled: boolean;
  onRemove: (deleteFiles: boolean) => void;
}

function describe(job: Job) {
  const again = job.subscription_id === null ? "" : " The channel won't download it again.";
  return (
    "Removing it from the list keeps the files on disk. Deleting files also deletes the " +
    `video and the files saved beside it (.nfo, thumbnail, subtitles).${again}`
  );
}

/** Asks whether to keep the files or delete them too. */
export function RemoveJobButton({ job, disabled, onRemove }: RemoveJobButtonProps) {
  const [open, setOpen] = useState(false);
  const name = job.title ?? job.url;

  function choose(deleteFiles: boolean) {
    setOpen(false);
    onRemove(deleteFiles);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" className="h-10" aria-label={`Remove ${name}`} disabled={disabled}>
          <Trash2 aria-hidden />
          Remove
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Remove this download?</DialogTitle>
          <DialogDescription className="truncate">{name}</DialogDescription>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">{describe(job)}</p>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="ghost" className="h-10">
              Keep it
            </Button>
          </DialogClose>
          <Button variant="outline" className="h-10" onClick={() => choose(false)}>
            Remove from list
          </Button>
          <Button variant="destructive" className="h-10" onClick={() => choose(true)}>
            Delete files
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
