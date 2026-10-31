import { FieldShell } from "@/components/field-shell";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface FieldLabels {
  label: string;
  hint?: React.ReactNode;
  error?: string;
}

export function FormField({
  label,
  hint,
  error,
  ...inputProps
}: FieldLabels & React.ComponentProps<typeof Input>) {
  return (
    <FieldShell label={label} hint={hint} error={error}>
      {(control) => <Input className="h-10" {...control} {...inputProps} />}
    </FieldShell>
  );
}

export function TextareaField({
  label,
  hint,
  error,
  ...textareaProps
}: FieldLabels & React.ComponentProps<typeof Textarea>) {
  return (
    <FieldShell label={label} hint={hint} error={error}>
      {(control) => <Textarea className="min-h-20 font-mono" {...control} {...textareaProps} />}
    </FieldShell>
  );
}

interface SelectFieldProps<T extends string> extends FieldLabels {
  value: T;
  choices: { value: T; label: string }[];
  disabled?: boolean;
  onValueChange: (value: T) => void;
}

/** A native select: works well with mobile pickers and screen readers. */
export function SelectField<T extends string>({
  label,
  hint,
  error,
  value,
  choices,
  disabled,
  onValueChange,
}: SelectFieldProps<T>) {
  return (
    <FieldShell label={label} hint={hint} error={error}>
      {(control) => (
        <select
          {...control}
          value={value}
          disabled={disabled}
          onChange={(event) => onValueChange(event.target.value as T)}
          className="h-10 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30"
        >
          {choices.map((choice) => (
            <option key={choice.value} value={choice.value}>
              {choice.label}
            </option>
          ))}
        </select>
      )}
    </FieldShell>
  );
}
