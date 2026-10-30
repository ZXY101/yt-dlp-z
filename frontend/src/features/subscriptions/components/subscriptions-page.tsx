import type { UseQueryResult } from "@tanstack/react-query";
import { Plus, Rss } from "lucide-react";
import { Link } from "react-router";

import { describeError } from "@/api/errors";
import { EmptyState } from "@/components/empty-state";
import { FormError } from "@/components/form-error";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { useSubscriptions } from "@/features/subscriptions/api";
import { SubscriptionCard } from "@/features/subscriptions/components/subscription-card";
import type { Subscription } from "@/features/subscriptions/types";

function AddButton() {
  return (
    <Button asChild size="lg" className="h-10">
      <Link to="/subscriptions/new">
        <Plus aria-hidden />
        Watch a channel
      </Link>
    </Button>
  );
}

function SubscriptionList({ subscriptions }: { subscriptions: UseQueryResult<Subscription[]> }) {
  if (subscriptions.isPending) {
    return <p className="text-sm text-muted-foreground">Loading subscriptions…</p>;
  }
  if (subscriptions.isError) {
    return <FormError message={describeError(subscriptions.error)} />;
  }
  if (subscriptions.data.length === 0) {
    return (
      <EmptyState
        icon={Rss}
        title="No channels watched yet"
        description="Add a YouTube channel and its new uploads are downloaded automatically, filtered the way you choose."
        action={{ label: "Add your first channel", to: "/subscriptions/new" }}
      />
    );
  }
  return (
    <ul className="space-y-3" aria-label="Subscriptions">
      {subscriptions.data.map((subscription) => (
        <SubscriptionCard key={subscription.id} subscription={subscription} />
      ))}
    </ul>
  );
}

export function SubscriptionsPage() {
  const subscriptions = useSubscriptions();
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader title="Subscriptions" action={<AddButton />} />
      <SubscriptionList subscriptions={subscriptions} />
    </div>
  );
}
