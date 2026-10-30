import { FormField } from "@/components/form-field";
import { type LimitField, useLimitField } from "@/features/settings/hooks/use-limit-field";
import type { AppSettings } from "@/features/settings/types";

// A week; longer values are almost certainly typos.
const MAX_HOURS = 168;

type RecordingSettings = AppSettings["recording"];

export function useRecordingFields(recording: RecordingSettings) {
  const options = { max: MAX_HOURS, optional: true };
  const fields = {
    part: useLimitField(recording.part_hours, options),
    max: useLimitField(recording.max_hours, options),
    fromStart: useLimitField(recording.from_start_max_hours, options),
  };

  function check() {
    return Object.values(fields)
      .map((field) => field.check())
      .every(Boolean);
  }

  function values(): RecordingSettings {
    return {
      part_hours: fields.part.parsed(),
      max_hours: fields.max.parsed(),
      from_start_max_hours: fields.fromStart.parsed(),
    };
  }

  return { fields, check, values };
}

type RecordingFieldsState = ReturnType<typeof useRecordingFields>;

function HoursField({ label, hint, field }: { label: string; hint: string; field: LimitField }) {
  return (
    <FormField
      label={label}
      inputMode="numeric"
      hint={hint}
      value={field.value}
      error={field.error}
      onChange={(event) => field.setValue(event.target.value)}
    />
  );
}

/** How live streams are recorded. Each recording keeps the values it started with. */
export function RecordingFields({ recording }: { recording: RecordingFieldsState }) {
  const { part, max, fromStart } = recording.fields;
  return (
    <fieldset className="space-y-6">
      <legend className="mb-4 text-lg font-medium">Recordings</legend>
      <HoursField
        label="New file every (hours)"
        hint="Splits long streams into parts, so endless streams stay manageable. Empty: one file per stream."
        field={part}
      />
      <HoursField
        label="Stop after (hours)"
        hint="Empty: record until the stream ends."
        field={max}
      />
      <HoursField
        label="Record from the start, unless live longer than (hours)"
        hint="Streams found after running longer are recorded from now. Empty: always from the start (up to 5 days of a 24/7 stream)."
        field={fromStart}
      />
    </fieldset>
  );
}
