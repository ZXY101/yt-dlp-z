import { ChevronDown } from "lucide-react";
import { useId, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface DisclosureProps {
  title: string;
  /** Short text after the title, e.g. how many options inside are set. */
  summary?: string;
  /** Unmount the content while closed (for large lists) instead of hiding it. */
  lazy?: boolean;
  /** Overrides the open state, e.g. to open every group while searching. */
  forceOpen?: boolean;
  children: React.ReactNode;
}

export function Disclosure({ title, summary, lazy, forceOpen, children }: DisclosureProps) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const expanded = forceOpen ?? open;

  return (
    <div className="space-y-3">
      <Button
        type="button"
        variant="ghost"
        className="h-10 px-2"
        aria-expanded={expanded}
        aria-controls={panelId}
        disabled={forceOpen !== undefined}
        onClick={() => setOpen(!open)}
      >
        <ChevronDown className={cn("transition-transform", expanded && "rotate-180")} aria-hidden />
        {title}
        {summary && <span className="font-normal text-muted-foreground">{summary}</span>}
      </Button>
      <div id={panelId} hidden={!expanded} className="space-y-4">
        {(expanded || !lazy) && children}
      </div>
    </div>
  );
}
