import { useState } from "react";

import { MAX_RECORDING_HOURS, type RecordingSettings } from "@/features/presets";
import { planRecording } from "@/features/downloads/recording-plan";
import type { JobCreate, MediaInfo } from "@/features/downloads/types";
import { useLimitField } from "@/hooks/use-limit-field";

interface RecordingChoiceInput {
  media: MediaInfo | undefined;
  /** When the link check answered (ms). */
  checkedAt: number;
  /** The chosen preset's recording settings, which fill the fields in. */
  recording: RecordingSettings;
  presetId: string;
}

function streamOf(media: MediaInfo | undefined) {
  return media?.kind === "live" || media?.kind === "upcoming" ? media : undefined;
}

/** Changes when the fields should be filled in afresh: another stream or another preset. */
function fillKey(presetId: string, stream: MediaInfo | undefined) {
  if (!stream) {
    return "";
  }
  return JSON.stringify([presetId, stream.kind, stream.title, stream.live_since, stream.starts_at]);
}

/** How a live or upcoming stream is recorded: filled in from the preset, changeable for this
 * recording. */
export function useRecordingChoice(input: RecordingChoiceInput) {
  const { media, recording, presetId, checkedAt } = input;
  const hourOptions = { max: MAX_RECORDING_HOURS, optional: true };
  const part = useLimitField(null, hourOptions);
  const max = useLimitField(null, hourOptions);
  const [fromStart, setFromStart] = useState(true);
  const [filledFor, setFilledFor] = useState("");
  const stream = streamOf(media);

  // Filled in during render rather than in an effect, so the fields never flash old values.
  const key = fillKey(presetId, stream);
  if (key !== filledFor) {
    setFilledFor(key);
    if (stream) {
      const plan = planRecording(recording, stream.live_since, checkedAt);
      setFromStart(plan.fromStart);
      part.reset(plan.partHours);
      max.reset(plan.maxHours);
    }
  }

  function check() {
    return !stream || [part.check(), max.check()].every(Boolean);
  }

  function request(): JobCreate["recording"] {
    if (!stream) {
      return null;
    }
    return {
      // Upcoming streams are always recorded from their start.
      from_start: stream.kind === "upcoming" || fromStart,
      starts_at: stream.starts_at,
      part_hours: part.parsed(),
      max_hours: max.parsed(),
      // From the preset; not changeable per recording.
      vod_after_hours: recording.vod_after_hours ?? null,
      vod_replace: recording.vod_replace ?? false,
    };
  }

  return { stream, checkedAt, fromStart, setFromStart, part, max, check, request };
}

export type RecordingChoiceState = ReturnType<typeof useRecordingChoice>;
