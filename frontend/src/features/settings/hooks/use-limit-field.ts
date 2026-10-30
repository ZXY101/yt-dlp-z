import { useState } from "react";

interface LimitOptions {
  max: number;
  // Empty is allowed and means "off" (the value is null).
  optional?: boolean;
}

function validateLimit(text: string, { max, optional }: LimitOptions) {
  if (optional && text.trim() === "") {
    return undefined;
  }
  const limit = Number(text);
  if (!Number.isInteger(limit) || limit < 1 || limit > max) {
    const range = `Enter a whole number from 1 to ${max}`;
    return optional ? `${range}, or leave it empty.` : `${range}.`;
  }
  return undefined;
}

/** A whole-number field from 1 to `max`; `check()` shows its error and says if it's valid. */
export function useLimitField(initial: number | null, options: LimitOptions) {
  const [value, setValue] = useState(initial === null ? "" : String(initial));
  const [error, setError] = useState<string>();

  function check() {
    const problem = validateLimit(value, options);
    setError(problem);
    return problem === undefined;
  }

  function parsed() {
    return value.trim() === "" ? null : Number(value);
  }

  return { value, setValue, error, check, parsed };
}

export type LimitField = ReturnType<typeof useLimitField>;
