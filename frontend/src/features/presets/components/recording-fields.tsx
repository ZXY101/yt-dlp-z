import { useState } from "react";

import { CheckboxField } from "@/components/checkbox-field";
import { FormField } from "@/components/form-field";
import { RadioOption } from "@/components/radio-option";
import { MAX_RECORDING_HOURS } from "@/features/presets/kinds";
import type { RecordingSettings } from "@/features/presets/types";
import { type LimitField, useLimitField } from "@/hooks/use-limit-field";

type LongStreams = RecordingSettings["long_streams"];

export function useRecordingFields(recording: RecordingSettings) {
  const options = { max: MAX_RECORDING_HOURS, optional: true };
  const fields = {
    part: useLimitField(recording.part_hours, options),
    max: useLimitField(recording.max_hours, options),
    fromStart: useLimitField(recording.from_start_max_hours, options),
    vodAfter: useLimitField(recording.vod_after_hours ?? null, options),
  };
  const [longStreams, setLongStreams] = useState<LongStreams>(recording.long_streams);
  const [vodReplace, setVodReplace] = useState(recording.vod_replace ?? false);

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
      vod_after_hours: fields.vodAfter.parsed(),
      vod_replace: vodReplace,
    };
  }

  return { fields, longStreams, setLongStreams, vodReplace, setVodReplace, check, values };
}

export type RecordingFieldsState = ReturnType<typeof useRecordingFields>;

export function HoursField({
  label,
  hint,
  field,
}: {
  label: string;
  hint: string;
  field: LimitField;
}) {
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

/** The VOD YouTube keeps after the stream: optional, downloaded some hours later. */
function VodFields({ recording }: { recording: RecordingFieldsState }) {
  const { vodAfter } = recording.fields;
  return (
    <>
      <HoursField
        label="Download the VOD afterwards (hours after the stream)"
        hint="Optional. Fills gaps a recording can have; YouTube needs time to process long streams. The VOD gets “(VOD)” in its name. Empty: no VOD."
        field={vodAfter}
      />
      {typedHours(vodAfter) !== null && (
        <CheckboxField
          label="Delete the recording once the VOD is saved"
          description="Only if the VOD is as long as the stream. If it's shorter, it may have been edited, so the recording stays. It also stays if the VOD can't be downloaded (members-only, not archived)."
          checked={recording.vodReplace}
          onCheckedChange={recording.setVodReplace}
        />
      )}
    </>
  );
}

/** How a preset records live streams. Each recording keeps the values it started with. */
export function RecordingFields({ recording }: { recording: RecordingFieldsState }) {
  const { part, max, fromStart } = recording.fields;
  const fromStartHours = typedHours(fromStart);
  return (
    <fieldset className="space-y-6">
      <legend className="mb-4 text-lg font-medium">Live stream recording</legend>
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
      <VodFields recording={recording} />
    </fieldset>
  );
}
