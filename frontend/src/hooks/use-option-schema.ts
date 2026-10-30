import { useQuery } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";

/** yt-dlp's options, read from the installed version. Changes only when yt-dlp does. */
export function useOptionSchema(enabled = true) {
  return useQuery({
    queryKey: ["options", "schema"],
    queryFn: () => unwrap(api.GET("/api/options/schema")),
    enabled,
    staleTime: Infinity,
  });
}
