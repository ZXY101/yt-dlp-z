import { Pause, Pencil, Play, RefreshCw, Trash2 } from "lucide-react";
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
import { describeCheck } from "@/features/subscriptions/format";
import type { Subscription } from "@/features/subscriptions/types";

function useCardActions(subscription: Subscription) {
  const check = useCheckSubscription();
  const update = useUpdateSubscription();
  const remove = useDeleteSubscription();
  const failed = [check, update, remove].find((mutation) => mutation.isError);

  function togglePaused() {
    const { id, preset_id, stream_preset_id, cookie_id, output_dir, filters, poll_minutes } =
      subscription;
    const body = { preset_id, stream_preset_id, cookie_id, output_dir, filters, poll_minutes };
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

function SubscriptionSummary({ subscription }: { subscription: Subscription }) {
  return (
    <div className="flex items-start gap-3">
      <div className="min-w-0 flex-1 space-y-1">
        <a
          href={subscription.url}
          target="_blank"
          rel="noreferrer"
          className="block truncate font-medium hover:underline"
        >
          {subscription.name}
        </a>
        <p className="text-xs text-muted-foreground">
          {describeCheck(subscription)} · every {subscription.poll_minutes} min
        </p>
        {subscription.last_error && (
          <p className="text-xs break-words text-destructive">{subscription.last_error}</p>
        )}
      </div>
      {!subscription.enabled && <Badge variant="secondary">Paused</Badge>}
    </div>
  );
}

export function SubscriptionCard({ subscription }: { subscription: Subscription }) {
  const actions = useCardActions(subscription);
  const { name } = subscription;
  return (
    <li className="space-y-3 rounded-xl border p-4">
      <SubscriptionSummary subscription={subscription} />
      <FormError message={actions.error} />
      <div className="flex flex-wrap justify-end gap-2">
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
    </li>
  );
}
