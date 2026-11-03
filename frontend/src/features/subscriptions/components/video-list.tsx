import { describeError } from "@/api/errors";
import { FormError } from "@/components/form-error";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useSetVideoIgnored, useSubscriptionVideos } from "@/features/subscriptions/api";
import { VIDEO_STATE_LABELS, formatRelative } from "@/features/subscriptions/format";
import type { Subscription, Video } from "@/features/subscriptions/types";

function videoDetail(video: Video) {
  if (video.reason) {
    return video.reason;
  }
  if (video.state === "upcoming" && video.release_at) {
    return `Starts ${formatRelative(video.release_at)}`;
  }
  return null;
}

// Videos still waiting, running or retried can be skipped for good.
const IGNORABLE = new Set<Video["state"]>(["queued", "upcoming", "live", "failed"]);

function IgnoreButton({ video, subscriptionId }: { video: Video; subscriptionId: number }) {
  const update = useSetVideoIgnored(subscriptionId);
  const ignored = video.state === "ignored";
  if (!ignored && !IGNORABLE.has(video.state)) {
    return null;
  }
  const text = ignored ? "Allow again" : "Don't download";
  return (
    <Button
      variant="ghost"
      size="sm"
      aria-label={`${text}: ${video.title}`}
      disabled={update.isPending}
      onClick={() => update.mutate({ videoId: video.id, ignored: !ignored })}
    >
      {text}
    </Button>
  );
}

function VideoRow({ video, subscriptionId }: { video: Video; subscriptionId: number }) {
  const detail = videoDetail(video);
  return (
    <li className="flex items-start gap-3 py-2">
      <div className="min-w-0 flex-1">
        <a
          href={`https://www.youtube.com/watch?v=${video.video_id}`}
          target="_blank"
          rel="noreferrer"
          className="block truncate text-sm hover:underline"
        >
          {video.title}
        </a>
        {detail && <p className="text-xs break-words text-muted-foreground">{detail}</p>}
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1">
        <Badge variant={video.state === "failed" ? "destructive" : "secondary"}>
          {VIDEO_STATE_LABELS[video.state]}
        </Badge>
        <IgnoreButton video={video} subscriptionId={subscriptionId} />
      </div>
    </li>
  );
}

function VideoRows({ subscription }: { subscription: Subscription }) {
  const videos = useSubscriptionVideos(subscription.id, subscription.checking);
  if (videos.isPending) {
    return <p className="text-sm text-muted-foreground">Loading videos…</p>;
  }
  if (videos.isError) {
    return <FormError message={describeError(videos.error)} />;
  }
  if (videos.data.length === 0) {
    return <p className="text-sm text-muted-foreground">No videos seen yet.</p>;
  }
  return (
    <ul className="divide-y" aria-label="Recent videos">
      {videos.data.map((video) => (
        <VideoRow key={video.id} video={video} subscriptionId={subscription.id} />
      ))}
    </ul>
  );
}

/** What the subscription did with each recent upload, so skipped videos can be explained. */
export function VideoList({ subscription }: { subscription: Subscription }) {
  return (
    <section className="space-y-2" aria-labelledby="videos-heading">
      <h2 id="videos-heading" className="text-base font-semibold">
        Recent videos
      </h2>
      <VideoRows subscription={subscription} />
    </section>
  );
}
