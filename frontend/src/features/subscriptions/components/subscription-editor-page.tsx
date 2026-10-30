import { Link, useParams } from "react-router";

import { describeError } from "@/api/errors";
import { CheckboxField } from "@/components/checkbox-field";
import { FolderField } from "@/components/download-options/folder-field";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { useSubscriptions } from "@/features/subscriptions/api";
import { FilterFields } from "@/features/subscriptions/components/filter-fields";
import { LinkFields } from "@/features/subscriptions/components/link-fields";
import { VideoList } from "@/features/subscriptions/components/video-list";
import { MAX_BACKFILL, MIN_POLL_MINUTES } from "@/features/subscriptions/form-values";
import { useSubscriptionForm } from "@/features/subscriptions/hooks/use-subscription-form";
import type { Subscription } from "@/features/subscriptions/types";

function ChannelFields({ form }: { form: ReturnType<typeof useSubscriptionForm> }) {
  const { values, errors, change } = form;
  return (
    <>
      <FormField
        label="Channel"
        placeholder="https://www.youtube.com/@channel or @channel"
        autoComplete="off"
        spellCheck={false}
        value={values.channel}
        error={errors.channel}
        onChange={(event) => change({ channel: event.target.value })}
      />
      <FormField
        label="Download recent uploads now"
        inputMode="numeric"
        hint={`How many of the newest uploads to download right away (0 to ${MAX_BACKFILL}). Older ones are skipped.`}
        value={values.backfill}
        error={errors.backfill}
        onChange={(event) => change({ backfill: event.target.value })}
      />
    </>
  );
}

function SubscriptionForm({ subscription }: { subscription: Subscription | null }) {
  const form = useSubscriptionForm(subscription);
  const { values, errors, change, save } = form;

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    form.submit();
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit} noValidate>
      <FormError message={save.isError ? describeError(save.error) : null} />
      {subscription === null && <ChannelFields form={form} />}
      <LinkFields values={values} onChange={change} />
      <FolderField value={values.outputDir} onChange={(outputDir) => change({ outputDir })} />
      <FormField
        label="Check every (minutes)"
        inputMode="numeric"
        hint={`At least ${MIN_POLL_MINUTES}. Checking often makes rate limits more likely.`}
        value={values.pollMinutes}
        error={errors.pollMinutes}
        onChange={(event) => change({ pollMinutes: event.target.value })}
      />
      <CheckboxField
        label="Watch this channel"
        description="Turn off to pause checking without losing the settings."
        checked={values.enabled}
        onCheckedChange={(enabled) => change({ enabled })}
      />
      <FilterFields values={values} errors={errors} onChange={change} />
      <div className="flex flex-wrap gap-2">
        <Button type="submit" size="lg" className="h-10" disabled={save.isPending}>
          {save.isPending ? "Saving…" : "Save subscription"}
        </Button>
        <Button asChild variant="ghost" size="lg" className="h-10">
          <Link to="/subscriptions">Cancel</Link>
        </Button>
      </div>
    </form>
  );
}

function EditorContent({ subscriptionId }: { subscriptionId: number | null }) {
  const subscriptions = useSubscriptions();
  if (subscriptionId === null) {
    return <SubscriptionForm subscription={null} />;
  }
  if (subscriptions.isPending) {
    return <p className="text-sm text-muted-foreground">Loading subscription…</p>;
  }
  if (subscriptions.isError) {
    return <FormError message={describeError(subscriptions.error)} />;
  }
  const subscription = subscriptions.data.find((item) => item.id === subscriptionId);
  if (!subscription) {
    return <FormError message="This subscription doesn't exist any more." />;
  }
  return (
    <>
      <p className="text-sm break-words text-muted-foreground">{subscription.name}</p>
      <SubscriptionForm key={subscription.id} subscription={subscription} />
      <VideoList subscription={subscription} />
    </>
  );
}

export function SubscriptionEditorPage() {
  const { subscriptionId } = useParams();
  const id = subscriptionId === undefined ? null : Number(subscriptionId);
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader title={id === null ? "Watch a channel" : "Edit subscription"} />
      <EditorContent subscriptionId={id} />
    </div>
  );
}
