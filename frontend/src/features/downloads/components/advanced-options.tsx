import { ChevronDown } from "lucide-react";
import { useId, useState } from "react";

import { FormField, TextareaField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import type { DownloadForm } from "@/features/downloads/hooks/use-download-form";
import { cn } from "@/lib/utils";

export function AdvancedOptions({ form }: { form: DownloadForm }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();

  return (
    <div className="space-y-4">
      <Button
        type="button"
        variant="ghost"
        className="h-10 px-2"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen(!open)}
      >
        <ChevronDown className={cn("transition-transform", open && "rotate-180")} aria-hidden />
        Advanced options
      </Button>
      <div id={panelId} hidden={!open} className="space-y-4">
        <FormField
          label="File name template"
          placeholder="%(title)s [%(id)s].%(ext)s"
          hint="A yt-dlp output template. Sub-folders are allowed, e.g. %(uploader)s/%(title)s.%(ext)s."
          value={form.choices.outputTemplate}
          onChange={(event) => form.updateChoices({ outputTemplate: event.target.value })}
        />
        <TextareaField
          label="Extra yt-dlp options"
          placeholder="--limit-rate 2M --embed-chapters"
          hint="Any yt-dlp command-line options. Options that run programs or use files outside the download folder are blocked."
          spellCheck={false}
          value={form.fields.extraArgs}
          onChange={(event) => form.setters.setExtraArgs(event.target.value)}
        />
      </div>
    </div>
  );
}
