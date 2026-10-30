import { useState } from "react";

import { FormField } from "@/components/form-field";
import { RadioOption } from "@/components/radio-option";
import { type LimitField, useLimitField } from "@/features/settings/hooks/use-limit-field";
import type { AppSettings } from "@/features/settings/types";

// A week; longer values are almost certainly typos.
const MAX_HOURS = 168;

type RecordingSettings = AppSettings["recording"];
type LongStreams = RecordingSettings["long_streams"];

export function useLiveStreamFields(recording: RecordingSettings) {
  const options = { max: MAX_HOURS, optional: true };
  const fields = {
    part: useLimitField(recording.part_hours, options),
    max: useLimitField(recording.max_hours, options),
    fromStart: useLimitField(recording.from_start_max_hours, options),
  };
  const [longStreams, setLongStreams] = useState<LongStreams>(recording.long_streams);

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
      long_streams: longStreams,
    };
  }

  return { fields, longStreams, setLongStreams, check, values };
}

type LiveStreamFieldsState = ReturnType<typeof useLiveStreamFields>;

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

/** The hours typed into a field, while they're a valid number. */
function typedHours(field: LimitField) {
  return /^\d+$/.test(field.value.trim()) && Number(field.value) > 0 ? Number(field.value) : null;
}

interface LongStreamsChoiceProps {
  hours: number;
  value: LongStreams;
  onChange: (value: LongStreams) => void;
}

function LongStreamsChoice({ hours, value, onChange }: LongStreamsChoiceProps) {
  const unit = hours === 1 ? "hour" : "hours";
  return (
    <fieldset className="space-y-1">
      <legend className="mb-1 text-sm font-medium">
        Streams live longer than {hours} {unit} when found
      </legend>
      <RadioOption
        name="long-streams"
        label="Record from now"
        checked={value === "from_now"}
        onSelect={() => onChange("from_now")}
      />
      <RadioOption
        name="long-streams"
        label={`Record their first ${hours} ${unit}`}
        checked={value === "first_hours"}
        onSelect={() => onChange("first_hours")}
      />
    </fieldset>
  );
}

interface LiveStreamFieldsProps {
  recording: LiveStreamFieldsState;
  // Recordings at the same time; saved apart from the other recording settings.
  concurrent: LimitField;
}

/** How live streams are recorded. Each recording keeps the values it started with. */
export function LiveStreamFields({ recording, concurrent }: LiveStreamFieldsProps) {
  const { part, max, fromStart } = recording.fields;
  const fromStartHours = typedHours(fromStart);
  return (
    <fieldset className="space-y-6">
      <legend className="mb-4 text-lg font-medium">Live streams</legend>
      <FormField
        label="Recordings at the same time"
        inputMode="numeric"
        hint="Counted apart from downloads, so recordings never wait behind them."
        value={concurrent.value}
        error={concurrent.error}
        onChange={(event) => concurrent.setValue(event.target.value)}
      />
      <HoursField
        label="New file every (hours)"
        hint="Splits long streams into parts, so endless streams stay manageable. Empty: one file per stream."
        field={part}
      />
      <HoursField
        label="Stop after (hours)"
        hint="Counts hours of the stream. Empty: record until the stream ends."
        field={max}
      />
      <HoursField
        label="Record from the start, unless live longer than (hours)"
        hint="Empty: always from the start (up to 5 days of a 24/7 stream)."
        field={fromStart}
      />
      {fromStartHours !== null && (
        <LongStreamsChoice
          hours={fromStartHours}
          value={recording.longStreams}
          onChange={recording.setLongStreams}
        />
      )}
    </fieldset>
  );
}
