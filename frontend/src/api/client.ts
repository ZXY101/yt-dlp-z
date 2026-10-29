import createClient from "openapi-fetch";

import type { paths } from "@/api/generated/schema";
import { ApiError, errorMessage } from "@/api/errors";

export const api = createClient<paths>({
  baseUrl: window.location.origin,
  // Look fetch up on every call so tests can stub it after this module loads.
  fetch: (request) => globalThis.fetch(request),
});

interface FetchResult<T> {
  data?: T;
  error?: unknown;
  response: Response;
}

export async function unwrap<T>(request: Promise<FetchResult<T>>): Promise<T> {
  const { data, error, response } = await request;
  if (error !== undefined || !response.ok) {
    throw new ApiError(errorMessage(error), response.status);
  }
  return data as T;
}
