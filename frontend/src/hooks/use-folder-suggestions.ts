import { useQuery } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";

/** The folder part of what's typed so far: "music/al" → "music/". */
export function parentOf(value: string) {
  return value.slice(0, value.lastIndexOf("/") + 1);
}

/** Sub-folders of `parent` on the server. Errors (e.g. outside the allowed
 * folders) just mean no suggestions; the form reports bad folders on submit. */
export function useFolderSuggestions(parent: string, enabled: boolean) {
  const query = useQuery({
    queryKey: ["folders", parent],
    queryFn: () => unwrap(api.GET("/api/folders", { params: { query: { parent } } })),
    enabled,
    retry: false,
    staleTime: 30_000,
  });
  return query.data?.folders ?? [];
}
