import { RadioOption } from "@/components/radio-option";
import { formatStartTime } from "@/features/downloads/format";
import type { RecordingChoiceState } from "@/features/downloads/hooks/use-recording-choice";
import { formatLiveFor, liveForSeconds } from "@/features/downloads/recording-plan";
import type { MediaInfo } from "@/features/downloads/types";
import { HoursField } from "@/features/presets";

function liveText(stream: MediaInfo, checkedAt: number) {
  if (!stream.live_since) {
    return "This stream is live.";
  }
  const seconds = liveForSeconds(stream.live_since, checkedAt);
  return `This stream has been live for ${formatLiveFor(seconds)}.`;
}

function StartChoice({ recording }: { recording: RecordingChoiceState }) {
  return (
    <fieldset className="space-y-1">
      <legend className="mb-1 text-sm font-medium">Record it</legend>
      <RadioOption
        name="recording-start"
        label="From the start"
        checked={recording.fromStart}
        onSelect={() => recording.setFromStart(true)}
      />
      <RadioOption
        name="recording-start"
        label="From now"
        checked={!recording.fromStart}
        onSelect={() => recording.setFromStart(false)}
      />
    </fieldset>
  );
}

function StreamSummary({ stream, checkedAt }: { stream: MediaInfo; checkedAt: number }) {
  if (stream.kind === "live") {
    return <p className="text-sm">{liveText(stream, checkedAt)}</p>;
  }
  const when = stream.starts_at ? `, ${formatStartTime(stream.starts_at)}` : "";
  return <p className="text-sm">The recording starts when the stream does{when}.</p>;
}

/** Live and upcoming streams are recorded rather than downloaded. The fields start from the
 * preset's recording settings. */
export function RecordingChoice({ recording }: { recording: RecordingChoiceState }) {
  const { stream } = recording;
  if (!stream) {
    return null;
  }
  return (
    <div className="space-y-6">
      <StreamSummary stream={stream} checkedAt={recording.checkedAt} />
      {stream.kind === "live" && <StartChoice recording={recording} />}
      <div className="grid gap-6 sm:grid-cols-2">
        <HoursField label="New file every (hours)" hint="Empty: one file." field={recording.part} />
        <HoursField
          label="Stop after (hours)"
          hint="Empty: until the stream ends."
          field={recording.max}
        />
      </div>
    </div>
  );
}
