import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { api, unwrap } from "@/api/client";
import type { YtdlpInfo, YtdlpPreferences } from "@/features/settings/types";

const YTDLP_KEY = ["ytdlp"];
const UPDATE_POLL_MS = 1000;

export function useYtdlpInfo() {
  return useQuery({
    queryKey: YTDLP_KEY,
    queryFn: () => unwrap(api.GET("/api/ytdlp")),
    // Updates run in the background on the server; poll until one finishes.
    refetchInterval: (query) =>
      query.state.data?.update.state === "running" ? UPDATE_POLL_MS : false,
  });
}

/** A new yt-dlp changes the version shown elsewhere and the options it offers. */
export function useRefreshOnVersionChange(version: string | undefined) {
  const queryClient = useQueryClient();
  const previous = useRef(version);
  useEffect(() => {
    if (previous.current && version && previous.current !== version) {
      void queryClient.invalidateQueries({ queryKey: ["system"] });
      void queryClient.invalidateQueries({ queryKey: ["options", "schema"] });
    }
    previous.current = version;
  }, [queryClient, version]);
}

function useYtdlpMutation<T>(send: (value: T) => Promise<YtdlpInfo>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: send,
    onSuccess: (info) => queryClient.setQueryData(YTDLP_KEY, info),
  });
}

/** Shows the choice at once and puts it back if saving fails. */
export function useSaveYtdlpPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: YtdlpPreferences) => unwrap(api.PUT("/api/ytdlp/preferences", { body })),
    onMutate: async (body) => {
      // A refetch already on its way would overwrite the choice with the old value.
      await queryClient.cancelQueries({ queryKey: YTDLP_KEY });
      const previous = queryClient.getQueryData<YtdlpInfo>(YTDLP_KEY);
      if (previous) {
        queryClient.setQueryData(YTDLP_KEY, { ...previous, ...body });
      }
      return { previous };
    },
    onError: (_error, _body, context) => queryClient.setQueryData(YTDLP_KEY, context?.previous),
    onSuccess: (info) => queryClient.setQueryData(YTDLP_KEY, info),
  });
}

export function useCheckYtdlp() {
  return useYtdlpMutation(() => unwrap(api.POST("/api/ytdlp/check")));
}

export function useStartYtdlpUpdate() {
  return useYtdlpMutation(() => unwrap(api.POST("/api/ytdlp/update")));
}

export function useRemoveYtdlpUpdate() {
  return useYtdlpMutation(() => unwrap(api.DELETE("/api/ytdlp/update")));
}
