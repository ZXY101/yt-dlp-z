import { CircleAlert, LoaderCircle } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { formatDuration, formatStartTime } from "@/features/downloads/format";
import type { LinkCheck } from "@/features/downloads/hooks/use-link-check";
import type { MediaInfo } from "@/features/downloads/types";

function countText(media: MediaInfo) {
  if (media.kind === "channel") {
    return "Channel";
  }
  if (media.entry_count === null) {
    return "Playlist";
  }
  return `Playlist · ${media.entry_count} ${media.entry_count === 1 ? "video" : "videos"}`;
}

function kindText(media: MediaInfo) {
  if (media.kind === "live") {
    return "Live now";
  }
  if (media.kind === "upcoming") {
    return media.starts_at ? `Starts ${formatStartTime(media.starts_at)}` : "Upcoming stream";
  }
  if (media.kind === "playlist" || media.kind === "channel") {
    return countText(media);
  }
  return media.duration === null ? null : formatDuration(media.duration);
}

function detailsText(media: MediaInfo) {
  const parts = [media.uploader, media.site, kindText(media)];
  return parts.filter(Boolean).join(" · ");
}

function MediaCard({ media }: { media: MediaInfo }) {
  return (
    <div className="flex gap-3 rounded-lg border p-3">
      {media.thumbnail && (
        <img
          src={media.thumbnail}
          alt=""
          referrerPolicy="no-referrer"
          className="aspect-video w-28 shrink-0 rounded-md bg-muted object-cover sm:w-36"
        />
      )}
      <div className="min-w-0 space-y-1">
        <p className="line-clamp-2 text-sm font-medium break-words">{media.title ?? "Untitled"}</p>
        <p className="text-xs text-muted-foreground">{detailsText(media)}</p>
      </div>
    </div>
  );
}

/** What the link check found: a card for the media, or why the link won't work. */
export function MediaPreview({ check }: { check: LinkCheck }) {
  if (check.status === "checking") {
    return (
      <output className="flex items-center gap-2 text-sm text-muted-foreground">
        <LoaderCircle className="size-4 animate-spin" aria-hidden />
        Checking link…
      </output>
    );
  }
  if (check.status === "failed") {
    return (
      <Alert variant="destructive">
        <CircleAlert aria-hidden />
        <AlertDescription>Can't download this link: {check.message}</AlertDescription>
      </Alert>
    );
  }
  if (check.status !== "ready") {
    return null;
  }
  return (
    <output className="block" aria-label="Media details">
      <MediaCard media={check.media} />
    </output>
  );
}
