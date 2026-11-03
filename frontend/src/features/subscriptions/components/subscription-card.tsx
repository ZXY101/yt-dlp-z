import { ChevronRight, ExternalLink, Pause, Pencil, Play, RefreshCw, Trash2 } from "lucide-react";
import { useId, useState } from "react";
import { Link } from "react-router";

import { describeError } from "@/api/errors";
import { ConfirmButton } from "@/components/confirm-button";
import { FormError } from "@/components/form-error";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  useCheckSubscription,
  useDeleteSubscription,
  useUpdateSubscription,
} from "@/features/subscriptions/api";
import { SubscriptionDownloads } from "@/features/subscriptions/components/subscription-downloads";
import { describeCheck } from "@/features/subscriptions/format";
import type { Subscription } from "@/features/subscriptions/types";

function useCardActions(subscription: Subscription) {
  const check = useCheckSubscription();
  const update = useUpdateSubscription();
  const remove = useDeleteSubscription();
  const failed = [check, update, remove].find((mutation) => mutation.isError);

  function togglePaused() {
    const { id, preset_id, stream_preset_id, cookie_id, output_dir, filters } = subscription;
    const { poll_minutes, keep_days } = subscription;
    const body = {
      preset_id,
      stream_preset_id,
      cookie_id,
      output_dir,
      filters,
      poll_minutes,
      keep_days,
    };
    update.mutate({ id, body: { ...body, enabled: !subscription.enabled } });
  }

  return {
    check: () => check.mutate(subscription.id),
    togglePaused,
    remove: () => remove.mutate(subscription.id),
    error: failed ? describeError(failed.error) : null,
  };
}

function PauseButton({
  subscription,
  onClick,
}: {
  subscription: Subscription;
  onClick: () => void;
}) {
  const label = subscription.enabled ? "Pause" : "Resume";
  return (
    <Button
      variant="ghost"
      className="h-10"
      aria-label={`${label} ${subscription.name}`}
      onClick={onClick}
    >
      {subscription.enabled ? <Pause aria-hidden /> : <Play aria-hidden />}
      {label}
    </Button>
  );
}

interface SummaryProps {
  subscription: Subscription;
  open: boolean;
  panelId: string;
  onToggle: () => void;
}

/** The whole summary is the expand button, so a tap anywhere on it opens the downloads. */
function SubscriptionSummary({ subscription, open, panelId, onToggle }: SummaryProps) {
  return (
    <button
      type="button"
      className="flex w-full cursor-pointer items-start gap-3 rounded-md text-left focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
      aria-expanded={open}
      aria-controls={panelId}
      onClick={onToggle}
    >
      <ChevronRight
        aria-hidden
        className={`mt-0.5 size-4 shrink-0 text-muted-foreground transition-transform ${open ? "rotate-90" : ""}`}
      />
      <span className="min-w-0 flex-1 space-y-1">
        <span className="block truncate font-medium">{subscription.name}</span>
        <span className="block text-xs text-muted-foreground">
          {describeCheck(subscription)} · every {subscription.poll_minutes} min
        </span>
        {subscription.last_error && (
          <span className="block text-xs break-words text-destructive">
            {subscription.last_error}
          </span>
        )}
      </span>
      {subscription.kind === "playlist" && <Badge variant="outline">Playlist</Badge>}
      {!subscription.enabled && <Badge variant="secondary">Paused</Badge>}
    </button>
  );
}

function ChannelLink({ subscription }: { subscription: Subscription }) {
  return (
    <Button asChild variant="ghost" className="h-10">
      <a
        href={subscription.url}
        target="_blank"
        rel="noreferrer"
        aria-label={`Open ${subscription.name} on YouTube`}
      >
        <ExternalLink aria-hidden />
        YouTube
      </a>
    </Button>
  );
}

export function SubscriptionCard({ subscription }: { subscription: Subscription }) {
  const actions = useCardActions(subscription);
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const { name } = subscription;
  return (
    <li className="space-y-3 rounded-xl border p-4">
      <SubscriptionSummary
        subscription={subscription}
        open={open}
        panelId={panelId}
        onToggle={() => setOpen((value) => !value)}
      />
      <FormError message={actions.error} />
      <div className="flex flex-wrap justify-end gap-2">
        <ChannelLink subscription={subscription} />
        <Button
          variant="ghost"
          className="h-10"
          aria-label={`Check ${name} now`}
          disabled={subscription.checking}
          onClick={actions.check}
        >
          <RefreshCw aria-hidden className={subscription.checking ? "animate-spin" : undefined} />
          Check now
        </Button>
        <PauseButton subscription={subscription} onClick={actions.togglePaused} />
        <Button asChild variant="ghost" className="h-10">
          <Link to={`/subscriptions/${subscription.id}`} aria-label={`Edit ${name}`}>
            <Pencil aria-hidden />
            Edit
          </Link>
        </Button>
        <ConfirmButton
          trigger={
            <Button variant="ghost" className="h-10" aria-label={`Delete ${name}`}>
              <Trash2 aria-hidden />
              Delete
            </Button>
          }
          title={`Stop watching ${name}?`}
          description="Downloads already queued or finished stay. This can't be undone."
          confirmText="Delete"
          onConfirm={actions.remove}
        />
      </div>
      {open && <SubscriptionDownloads subscription={subscription} id={panelId} />}
    </li>
  );
}
