import { useId } from "react";

import { Label } from "@/components/ui/label";

interface FieldControlProps {
  id: string;
  "aria-invalid": boolean;
  "aria-describedby": string | undefined;
}

interface FieldShellProps {
  label: string;
  hint?: string;
  error?: string;
  children: (control: FieldControlProps) => React.ReactNode;
}

/** Label, hint and error around any form control, wired up for screen readers. */
export function FieldShell({ label, hint, error, children }: FieldShellProps) {
  const id = useId();
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  // The error replaces the hint rather than stacking under it.
  const showHint = Boolean(hint) && !error;
  const describedBy = [showHint && hintId, error && errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      {children({ id, "aria-invalid": Boolean(error), "aria-describedby": describedBy })}
      {showHint && (
        <p id={hintId} className="text-xs text-muted-foreground">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
