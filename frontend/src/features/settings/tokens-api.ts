import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";

const TOKENS_KEY = ["api-tokens"];

export function useApiTokens() {
  return useQuery({ queryKey: TOKENS_KEY, queryFn: () => unwrap(api.GET("/api/tokens")) });
}

export function useCreateApiToken() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => unwrap(api.POST("/api/tokens", { body: { name } })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TOKENS_KEY }),
  });
}

export function useRevokeApiToken() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      unwrap(api.DELETE("/api/tokens/{token_id}", { params: { path: { token_id: id } } })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TOKENS_KEY }),
  });
}
