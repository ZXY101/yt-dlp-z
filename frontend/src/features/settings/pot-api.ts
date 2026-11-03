import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";

const POT_KEY = ["ytdlp", "pot"];

export function usePotProvider() {
  return useQuery({ queryKey: POT_KEY, queryFn: () => unwrap(api.GET("/api/ytdlp/pot")) });
}

/** Checks the server and installs its plugin before saving; null turns PO tokens off. */
export function useSavePotProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (url: string | null) => unwrap(api.PUT("/api/ytdlp/pot", { body: { url } })),
    onSuccess: (saved) => queryClient.setQueryData(POT_KEY, saved),
  });
}

export function useTestPotProvider() {
  return useMutation({
    mutationFn: (url: string) => unwrap(api.POST("/api/ytdlp/pot/test", { body: { url } })),
  });
}
