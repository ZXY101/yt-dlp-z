import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";
import type { ProxyCreate, ProxySettings, ProxyUpdate } from "@/features/proxies/types";

const PROXIES_KEY = ["proxies"];
const PROXY_SETTINGS_KEY = ["proxy-settings"];

function proxyPath(proxyId: number) {
  return { params: { path: { proxy_id: proxyId } } };
}

export function useProxies() {
  return useQuery({ queryKey: PROXIES_KEY, queryFn: () => unwrap(api.GET("/api/proxies")) });
}

function useProxyMutation<T>(send: (input: T) => Promise<unknown>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: send,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROXIES_KEY }),
  });
}

export function useAddProxy() {
  return useProxyMutation((body: ProxyCreate) => unwrap(api.POST("/api/proxies", { body })));
}

export function useUpdateProxy() {
  return useProxyMutation(({ id, ...body }: ProxyUpdate & { id: number }) =>
    unwrap(api.PUT("/api/proxies/{proxy_id}", { ...proxyPath(id), body })),
  );
}

export function useDeleteProxy() {
  return useProxyMutation((id: number) =>
    unwrap(api.DELETE("/api/proxies/{proxy_id}", proxyPath(id))),
  );
}

/** Opens a page through the proxy; the result is saved on the proxy. */
export function useCheckProxy() {
  return useProxyMutation((id: number) =>
    unwrap(api.POST("/api/proxies/{proxy_id}/check", proxyPath(id))),
  );
}

export function useProxySettings() {
  return useQuery({
    queryKey: PROXY_SETTINGS_KEY,
    queryFn: () => unwrap(api.GET("/api/proxies/settings")),
  });
}

export function useSaveProxySettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ProxySettings) => unwrap(api.PUT("/api/proxies/settings", { body })),
    onSuccess: (saved) => queryClient.setQueryData(PROXY_SETTINGS_KEY, saved),
  });
}
