import { Info } from "lucide-react";

import { RadioOption } from "@/components/radio-option";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { MediaInfo } from "@/features/downloads/types";

interface PlaylistChoiceProps {
  videoInPlaylist: boolean;
  media: MediaInfo | undefined;
  wholePlaylist: boolean;
  onWholePlaylistChange: (wholePlaylist: boolean) => void;
}

function playlistNotice(media: MediaInfo) {
  if (media.kind === "channel") {
    return "This is a channel: every video, Short and stream on all its tabs will be downloaded.";
  }
  if (media.entry_count === null) {
    return "This is a playlist: every video in it will be downloaded.";
  }
  return `This is a playlist: all ${media.entry_count} videos in it will be downloaded.`;
}

function PlaylistNotice({ media }: { media: MediaInfo }) {
  return (
    // <output> announces the notice politely; the Alert's own role="alert" would interrupt.
    <output className="block">
      <Alert role="none">
        <Info aria-hidden="true" />
        <AlertDescription className="text-pretty text-foreground">
          {playlistNotice(media)}
        </AlertDescription>
      </Alert>
    </output>
  );
}

/** Asks what to download for playlist links, so a whole playlist is never a surprise. */
export function PlaylistChoice({
  videoInPlaylist,
  media,
  wholePlaylist,
  onWholePlaylistChange,
}: PlaylistChoiceProps) {
  if (videoInPlaylist) {
    return (
      <fieldset className="space-y-1">
        <legend className="mb-1 text-sm font-medium">This link is part of a playlist</legend>
        <RadioOption
          name="playlist-choice"
          label="Just this video"
          checked={!wholePlaylist}
          onSelect={() => onWholePlaylistChange(false)}
        />
        <RadioOption
          name="playlist-choice"
          label="The whole playlist"
          checked={wholePlaylist}
          onSelect={() => onWholePlaylistChange(true)}
        />
      </fieldset>
    );
  }
  if (media?.kind === "playlist" || media?.kind === "channel") {
    return <PlaylistNotice media={media} />;
  }
  return null;
}
