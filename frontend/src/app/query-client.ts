import { QueryClient } from "@tanstack/react-query";

export function createQueryClient() {
  return new QueryClient({
    // The API is local to the user, so failures are real errors worth showing
    // straight away rather than retrying.
    defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
  });
}
