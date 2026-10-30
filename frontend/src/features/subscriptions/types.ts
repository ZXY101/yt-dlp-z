import type { components } from "@/api/generated/schema";

export type Subscription = components["schemas"]["SubscriptionOut"];
export type SubscriptionCreate = components["schemas"]["SubscriptionCreate"];
export type SubscriptionUpdate = components["schemas"]["SubscriptionUpdate"];
export type ContentType = components["schemas"]["ContentType"];
export type Video = components["schemas"]["VideoOut"];
export type VideoState = Video["state"];
