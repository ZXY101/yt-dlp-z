import { SlidersHorizontal } from "lucide-react";

import type { OptionsProps } from "@/components/download-options/option-groups";
import { OptionsEditor } from "@/components/download-options/options-editor";
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
import { countSet } from "@/lib/download-options";

/** A button showing how many options are set, opening every yt-dlp option in a dialog. */
export function OptionsDialog({ options, onChange }: OptionsProps) {
  const setCount = countSet(options, Object.keys(options));
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button type="button" variant="outline" className="h-10">
          <SlidersHorizontal aria-hidden />
          All yt-dlp options
          {setCount > 0 && (
            <span className="font-normal text-muted-foreground">· {setCount} set</span>
          )}
        </Button>
      </DialogTrigger>
      <DialogContent className="flex h-[85dvh] flex-col gap-0 p-0 sm:max-w-4xl">
        <DialogHeader className="border-b p-4 pr-12">
          <DialogTitle>yt-dlp options</DialogTitle>
          <DialogDescription>Changes apply as you make them.</DialogDescription>
        </DialogHeader>
        <OptionsEditor options={options} onChange={onChange} />
        <DialogFooter className="mx-0 mb-0">
          <DialogClose asChild>
            <Button type="button" className="h-10">
              Done
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
