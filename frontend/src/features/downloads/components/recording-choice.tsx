import { Link } from "react-router";

import { RadioOption } from "@/components/radio-option";
import { formatStartTime } from "@/features/downloads/format";
import type { MediaInfo } from "@/features/downloads/types";

interface RecordingChoiceProps {
  media: MediaInfo;
  fromStart: boolean;
  onFromStartChange: (fromStart: boolean) => void;
}

function SettingsHint() {
  return (
    <p className="text-xs text-muted-foreground">
      Splitting into parts and the maximum length follow{" "}
      <Link to="/settings" className="underline underline-offset-2">
        Settings → Live streams
      </Link>
      .
    </p>
  );
}

/** Live and upcoming streams are recorded rather than downloaded. */
export function RecordingChoice({ media, fromStart, onFromStartChange }: RecordingChoiceProps) {
  if (media.kind === "upcoming") {
    const when = media.starts_at ? `, ${formatStartTime(media.starts_at)}` : "";
    return (
      <div className="space-y-1">
        <p className="text-sm">The recording starts when the stream does{when}.</p>
        <SettingsHint />
      </div>
    );
  }
  return (
    <fieldset className="space-y-1">
      <legend className="mb-1 text-sm font-medium">This stream is live. Record it</legend>
      <RadioOption
        name="recording-start"
        label="From the start"
        checked={fromStart}
        onSelect={() => onFromStartChange(true)}
      />
      <RadioOption
        name="recording-start"
        label="From now"
        checked={!fromStart}
        onSelect={() => onFromStartChange(false)}
      />
      <SettingsHint />
    </fieldset>
  );
}
