import { useId } from "react";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

interface CheckboxFieldProps {
  label: string;
  description?: string;
  checked: boolean;
  disabled?: boolean;
  onCheckedChange: (checked: boolean) => void;
}

export function CheckboxField({
  label,
  description,
  checked,
  disabled,
  onCheckedChange,
}: CheckboxFieldProps) {
  const id = useId();
  return (
    <div className={cn("flex min-h-10 gap-3 py-1", description ? "items-start" : "items-center")}>
      <Checkbox
        id={id}
        className="size-5"
        checked={checked}
        disabled={disabled}
        onCheckedChange={(state) => onCheckedChange(state === true)}
        aria-describedby={description ? `${id}-description` : undefined}
      />
      <div className="space-y-0.5">
        {/* leading-5 matches the box's height, so the text lines up with it. */}
        <Label htmlFor={id} className={cn("leading-5 break-all", !disabled && "cursor-pointer")}>
          {label}
        </Label>
        {description && (
          <p id={`${id}-description`} className="text-xs text-muted-foreground">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}
