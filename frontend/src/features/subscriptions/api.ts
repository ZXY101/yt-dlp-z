import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";
import type {
  Subscription,
  SubscriptionCreate,
  SubscriptionUpdate,
} from "@/features/subscriptions/types";

const SUBSCRIPTIONS_KEY = ["subscriptions"];
// A check runs in the background; poll until it's done.
const CHECKING_POLL_MS = 2000;

function subscriptionPath(subscriptionId: number) {
  return { params: { path: { subscription_id: subscriptionId } } };
}

function pollWhileChecking(subscriptions: Subscription[] | undefined) {
  return subscriptions?.some((item) => item.checking) ? CHECKING_POLL_MS : false;
}

export function useSubscriptions() {
  return useQuery({
    queryKey: SUBSCRIPTIONS_KEY,
    queryFn: () => unwrap(api.GET("/api/subscriptions")),
    refetchInterval: (query) => pollWhileChecking(query.state.data),
  });
}

export function useSubscriptionVideos(subscriptionId: number, checking: boolean) {
  return useQuery({
    queryKey: [...SUBSCRIPTIONS_KEY, subscriptionId, "videos"],
    queryFn: () =>
      unwrap(
        api.GET("/api/subscriptions/{subscription_id}/videos", subscriptionPath(subscriptionId)),
      ),
    refetchInterval: checking ? CHECKING_POLL_MS : false,
  });
}

function useSubscriptionMutation<T, R>(send: (input: T) => Promise<R>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: send,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: SUBSCRIPTIONS_KEY }),
  });
}

export function useCreateSubscription() {
  return useSubscriptionMutation((body: SubscriptionCreate) =>
    unwrap(api.POST("/api/subscriptions", { body })),
  );
}

export function useUpdateSubscription() {
  return useSubscriptionMutation(({ id, body }: { id: number; body: SubscriptionUpdate }) =>
    unwrap(api.PUT("/api/subscriptions/{subscription_id}", { ...subscriptionPath(id), body })),
  );
}

export function useDeleteSubscription() {
  return useSubscriptionMutation((id: number) =>
    unwrap(api.DELETE("/api/subscriptions/{subscription_id}", subscriptionPath(id))),
  );
}

export function useCheckSubscription() {
  return useSubscriptionMutation((id: number) =>
    unwrap(api.POST("/api/subscriptions/{subscription_id}/check", subscriptionPath(id))),
  );
}
