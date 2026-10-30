import { useState } from "react";

import { CheckboxField } from "@/components/checkbox-field";
import type { OptionSpec } from "@/components/download-options/option-search";
import { FormField, SelectField, TextareaField } from "@/components/form-field";
import type { OptionValue } from "@/lib/download-options";

interface OptionFieldProps {
  option: OptionSpec;
  value: OptionValue | undefined;
  onChange: (value: OptionValue | undefined) => void;
}

function labelOf(option: OptionSpec) {
  return option.metavar ? `${option.flag} ${option.metavar}` : option.flag;
}

function hintOf(option: OptionSpec) {
  return option.blocked_reason ? `Blocked: ${option.blocked_reason}` : option.help;
}

function toLines(value: OptionValue | undefined) {
  if (Array.isArray(value)) {
    return value.join("\n");
  }
  return typeof value === "string" ? value : "";
}

/** One value per line, kept as typed so blank lines don't vanish mid-edit. */
function RepeatableField({ option, value, onChange }: OptionFieldProps) {
  const [text, setText] = useState(() => toLines(value));

  function handleChange(next: string) {
    setText(next);
    onChange(next.split("\n").filter((line) => line.trim() !== ""));
  }

  return (
    <TextareaField
      label={labelOf(option)}
      hint={`${hintOf(option)} One value per line.`}
      disabled={Boolean(option.blocked_reason)}
      spellCheck={false}
      value={text}
      onChange={(event) => handleChange(event.target.value)}
    />
  );
}

function ChoiceField({ option, value, onChange }: OptionFieldProps) {
  const choices = [
    { value: "", label: "Not set" },
    ...(option.choices ?? []).map((choice) => ({ value: choice, label: choice })),
  ];
  return (
    <SelectField
      label={labelOf(option)}
      hint={hintOf(option)}
      disabled={Boolean(option.blocked_reason)}
      value={typeof value === "string" ? value : ""}
      choices={choices}
      onValueChange={(choice) => onChange(choice || undefined)}
    />
  );
}

export function OptionField(props: OptionFieldProps) {
  const { option, value, onChange } = props;
  const blocked = Boolean(option.blocked_reason);
  if (option.kind === "flag") {
    return (
      <CheckboxField
        label={option.flag}
        description={hintOf(option)}
        disabled={blocked}
        checked={value === true}
        onCheckedChange={(checked) => onChange(checked)}
      />
    );
  }
  if (option.kind === "choice") {
    return <ChoiceField {...props} />;
  }
  if (option.repeatable) {
    return <RepeatableField {...props} />;
  }
  return (
    <FormField
      label={labelOf(option)}
      hint={hintOf(option)}
      disabled={blocked}
      spellCheck={false}
      inputMode={option.kind === "number" ? "decimal" : undefined}
      value={typeof value === "string" || typeof value === "number" ? String(value) : ""}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}
