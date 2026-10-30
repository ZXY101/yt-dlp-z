import { describeError } from "@/api/errors";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { useMediaProbe } from "@/features/downloads/api";
import type { MediaInfo, MediaProbeRequest } from "@/features/downloads/types";
import { validateUrl } from "@/features/downloads/validate-url";

// Waits for typing to pause, so each keystroke doesn't start a yt-dlp run.
const CHECK_DELAY_MS = 600;

export type LinkCheck =
  | { status: "empty" }
  | { status: "invalid"; message: string }
  | { status: "checking" }
  | { status: "failed"; message: string }
  | { status: "ready"; media: MediaInfo };

interface LinkCheckInput {
  url: string;
  cookieId: number | null;
  noPlaylist: boolean;
  /** Check without waiting, e.g. for a pasted link (the wait is only for typing). */
  immediate: boolean;
}

function probeRequest({ url, cookieId, noPlaylist }: LinkCheckInput): MediaProbeRequest {
  return { url: url.trim(), cookie_id: cookieId, no_playlist: noPlaylist };
}

/** The probe request as a string, or "" when there is nothing valid to check. Debounced as
 * a string: a new request object every render would restart the timer. */
function requestKey(input: LinkCheckInput, invalid: string | undefined) {
  return input.url.trim() && !invalid ? JSON.stringify(probeRequest(input)) : "";
}

function probeResult(probe: ReturnType<typeof useMediaProbe>): LinkCheck {
  if (probe.isPending) {
    return { status: "checking" };
  }
  if (probe.isError) {
    return { status: "failed", message: describeError(probe.error) };
  }
  return { status: "ready", media: probe.data };
}

/** Checks the link with yt-dlp as it is typed, so problems show before anything is queued. */
export function useLinkCheck(input: LinkCheckInput): LinkCheck {
  const invalid = input.url.trim() ? validateUrl(input.url) : undefined;
  const key = requestKey(input, invalid);
  const debouncedKey = useDebouncedValue(key, CHECK_DELAY_MS);
  const debouncedInvalid = useDebouncedValue(invalid, CHECK_DELAY_MS);
  const settledKey = input.immediate ? key : debouncedKey;
  const settledInvalid = input.immediate ? invalid : debouncedInvalid;
  const probe = useMediaProbe(settledKey ? (JSON.parse(settledKey) as MediaProbeRequest) : null);

  if (invalid) {
    return settledInvalid ? { status: "invalid", message: settledInvalid } : { status: "empty" };
  }
  if (!key) {
    return { status: "empty" };
  }
  return settledKey === key ? probeResult(probe) : { status: "checking" };
}
