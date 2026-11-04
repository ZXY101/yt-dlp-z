import { useState } from "react";

import { FormField } from "@/components/form-field";

interface NumberFieldProps {
  label: string;
  hint?: string;
  value: number;
  min: number;
  max: number;
  /** Fractions are fine, e.g. for seconds. Otherwise only whole numbers count. */
  decimals?: boolean;
  onChange: (value: number) => void;
}

function problemWith(text: string, { min, max, decimals }: NumberFieldProps) {
  const parsed = Number(text);
  const allowed = decimals || Number.isInteger(parsed);
  if (text.trim() === "" || !allowed || parsed < min || parsed > max) {
    return `Enter a${decimals ? " number" : " whole number"} from ${min} to ${max}.`;
  }
  return undefined;
}

/** Keeps what's being typed; only valid numbers reach the form. Invalid text shows an error
 * until the field loses focus, then goes back to the number the form has. */
export function NumberField(props: NumberFieldProps) {
  const { label, hint, value, onChange } = props;
  const [text, setText] = useState(String(value));
  const error = problemWith(text, props);

  function handleChange(next: string) {
    setText(next);
    if (problemWith(next, props) === undefined) {
      onChange(Number(next));
    }
  }

  return (
    <FormField
      label={label}
      hint={hint}
      inputMode={props.decimals ? "decimal" : "numeric"}
      value={text}
      error={error}
      onChange={(event) => handleChange(event.target.value)}
      onBlur={() => setText(String(value))}
    />
  );
}
