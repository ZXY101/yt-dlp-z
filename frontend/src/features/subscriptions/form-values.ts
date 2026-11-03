import type {
  ContentType,
  Subscription,
  SubscriptionCreate,
  SubscriptionUpdate,
} from "@/features/subscriptions/types";

export const MIN_POLL_MINUTES = 5;
const MAX_POLL_MINUTES = 7 * 24 * 60;
export const MAX_BACKFILL = 15;
export const MAX_KEEP_DAYS = 3650;
const SECONDS_PER_MINUTE = 60;

/** Form state: numbers stay text until submit so half-typed values aren't mangled. */
export interface SubscriptionFormValues {
  channel: string;
  backfill: string;
  presetId: number | null;
  streamPresetId: number | null;
  cookieId: number | null;
  outputDir: string;
  pollMinutes: string;
  enabled: boolean;
  /** Empty keeps downloads for good. */
  keepDays: string;
  contentTypes: ContentType[];
  titleInclude: string;
  titleExclude: string;
  minMinutes: string;
  maxMinutes: string;
  publishedAfter: string;
  includeMembersOnly: boolean;
}

export type FormErrors = Partial<Record<keyof SubscriptionFormValues, string>>;

export const EMPTY_FORM: SubscriptionFormValues = {
  channel: "",
  backfill: "0",
  presetId: null,
  streamPresetId: null,
  cookieId: null,
  outputDir: "",
  pollMinutes: "10",
  enabled: true,
  keepDays: "",
  contentTypes: ["video"],
  titleInclude: "",
  titleExclude: "",
  minMinutes: "",
  maxMinutes: "",
  publishedAfter: "",
  includeMembersOnly: false,
};

function minutesText(seconds: number | null | undefined) {
  return seconds === null || seconds === undefined ? "" : String(seconds / SECONDS_PER_MINUTE);
}

export function formFromSubscription(subscription: Subscription): SubscriptionFormValues {
  const { filters } = subscription;
  return {
    channel: subscription.url,
    backfill: String(subscription.backfill),
    presetId: subscription.preset_id ?? null,
    streamPresetId: subscription.stream_preset_id ?? null,
    cookieId: subscription.cookie_id ?? null,
    outputDir: subscription.output_dir ?? "",
    pollMinutes: String(subscription.poll_minutes),
    enabled: subscription.enabled,
    keepDays: subscription.keep_days ? String(subscription.keep_days) : "",
    contentTypes: filters.content_types,
    titleInclude: filters.title_include ?? "",
    titleExclude: filters.title_exclude ?? "",
    minMinutes: minutesText(filters.min_duration),
    maxMinutes: minutesText(filters.max_duration),
    publishedAfter: filters.published_after ?? "",
    includeMembersOnly: filters.include_members_only,
  };
}

function wholeNumberError(text: string, min: number, max: number) {
  const value = Number(text);
  if (text.trim() === "" || !Number.isInteger(value) || value < min || value > max) {
    return `Enter a whole number from ${min} to ${max}.`;
  }
  return undefined;
}

function minutesError(text: string) {
  if (text.trim() === "") {
    return undefined;
  }
  const value = Number(text);
  return Number.isFinite(value) && value >= 0 ? undefined : "Enter a number of minutes.";
}

export function validateForm(values: SubscriptionFormValues, isNew: boolean): FormErrors {
  const errors: FormErrors = {
    pollMinutes: wholeNumberError(values.pollMinutes, MIN_POLL_MINUTES, MAX_POLL_MINUTES),
    minMinutes: minutesError(values.minMinutes),
    maxMinutes: minutesError(values.maxMinutes),
    contentTypes: values.contentTypes.length === 0 ? "Pick at least one." : undefined,
    keepDays: values.keepDays.trim()
      ? wholeNumberError(values.keepDays, 1, MAX_KEEP_DAYS)
      : undefined,
  };
  if (isNew) {
    errors.channel = values.channel.trim() ? undefined : "Enter a channel URL or @handle.";
    errors.backfill = wholeNumberError(values.backfill, 0, MAX_BACKFILL);
  }
  return Object.fromEntries(Object.entries(errors).filter(([, error]) => error)) as FormErrors;
}

function secondsOrNull(minutes: string) {
  return minutes.trim() === "" ? null : Math.round(Number(minutes) * SECONDS_PER_MINUTE);
}

export function updateBody(values: SubscriptionFormValues): SubscriptionUpdate {
  return {
    preset_id: values.presetId,
    stream_preset_id: values.streamPresetId,
    cookie_id: values.cookieId,
    output_dir: values.outputDir.trim() || null,
    poll_minutes: Number(values.pollMinutes),
    enabled: values.enabled,
    keep_days: values.keepDays.trim() ? Number(values.keepDays) : null,
    filters: {
      content_types: values.contentTypes,
      title_include: values.titleInclude.trim() || null,
      title_exclude: values.titleExclude.trim() || null,
      min_duration: secondsOrNull(values.minMinutes),
      max_duration: secondsOrNull(values.maxMinutes),
      published_after: values.publishedAfter || null,
      include_members_only: values.includeMembersOnly,
    },
  };
}

export function createBody(values: SubscriptionFormValues): SubscriptionCreate {
  return {
    ...updateBody(values),
    channel: values.channel.trim(),
    backfill: Number(values.backfill),
  };
}
