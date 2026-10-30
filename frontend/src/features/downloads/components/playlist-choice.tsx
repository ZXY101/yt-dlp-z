import { Info } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import type { PlaylistLinkKind } from "@/features/downloads/playlist-link";

interface PlaylistChoiceProps {
  kind: PlaylistLinkKind | undefined;
  wholePlaylist: boolean;
  onWholePlaylistChange: (wholePlaylist: boolean) => void;
}

const NOTICES = {
  playlist: "This is a playlist: every video in it will be downloaded.",
  channel: "This is a channel: every video on it will be downloaded.",
};

/** Asks what to download for playlist links, so a whole playlist is never a surprise. */
export function PlaylistChoice({
  kind,
  wholePlaylist,
  onWholePlaylistChange,
}: PlaylistChoiceProps) {
  if (kind === "playlist" || kind === "channel") {
    return (
      // <output> announces the notice politely; the Alert's own role="alert" would interrupt.
      <output className="block">
        <Alert role="none">
          <Info aria-hidden="true" />
          <AlertDescription className="text-pretty text-foreground">
            {NOTICES[kind]}
          </AlertDescription>
        </Alert>
      </output>
    );
  }
  if (kind !== "video-in-playlist") {
    return null;
  }
  return (
    <fieldset className="space-y-1">
      <legend className="mb-1 text-sm font-medium">This link is part of a playlist</legend>
      <RadioOption
        label="Just this video"
        checked={!wholePlaylist}
        onSelect={() => onWholePlaylistChange(false)}
      />
      <RadioOption
        label="The whole playlist"
        checked={wholePlaylist}
        onSelect={() => onWholePlaylistChange(true)}
      />
    </fieldset>
  );
}

interface RadioOptionProps {
  label: string;
  checked: boolean;
  onSelect: () => void;
}

function RadioOption({ label, checked, onSelect }: RadioOptionProps) {
  return (
    <label className="flex min-h-10 cursor-pointer items-center gap-3 text-sm">
      <input
        type="radio"
        name="playlist-choice"
        className="size-5 cursor-pointer accent-primary"
        checked={checked}
        onChange={onSelect}
      />
      {label}
    </label>
  );
}
