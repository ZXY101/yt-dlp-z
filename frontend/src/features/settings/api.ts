import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";
import type { AppSettings } from "@/features/settings/types";

const SETTINGS_KEY = ["settings"];

export function useAppSettings() {
  return useQuery({ queryKey: SETTINGS_KEY, queryFn: () => unwrap(api.GET("/api/settings")) });
}

export function useSaveAppSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: AppSettings) => unwrap(api.PUT("/api/settings", { body })),
    onSuccess: (saved) => queryClient.setQueryData(SETTINGS_KEY, saved),
  });
}
