import { useId } from "react";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

interface CheckboxFieldProps {
  label: string;
  description?: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}

export function CheckboxField({
  label,
  description,
  checked,
  onCheckedChange,
}: CheckboxFieldProps) {
  const id = useId();
  return (
    <div className="flex min-h-10 items-start gap-3 py-1">
      <Checkbox
        id={id}
        className="mt-0.5 size-5"
        checked={checked}
        onCheckedChange={(state) => onCheckedChange(state === true)}
        aria-describedby={description ? `${id}-description` : undefined}
      />
      <div className="space-y-0.5">
        <Label htmlFor={id}>{label}</Label>
        {description && (
          <p id={`${id}-description`} className="text-xs text-muted-foreground">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}
