import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";

const COOKIES_KEY = ["cookies"];

function cookiePath(cookieId: number) {
  return { params: { path: { cookie_id: cookieId } } };
}

export function useCookieFiles() {
  return useQuery({ queryKey: COOKIES_KEY, queryFn: () => unwrap(api.GET("/api/cookies")) });
}

function useCookieMutation<T>(send: (input: T) => Promise<unknown>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: send,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: COOKIES_KEY }),
  });
}

export function useUploadCookieFile() {
  return useCookieMutation((body: { name: string; content: string }) =>
    unwrap(api.POST("/api/cookies", { body })),
  );
}

export function useReplaceCookieFile() {
  return useCookieMutation(({ id, ...body }: { id: number; name: string; content: string }) =>
    unwrap(api.PUT("/api/cookies/{cookie_id}", { ...cookiePath(id), body })),
  );
}

export function useDeleteCookieFile() {
  return useCookieMutation((id: number) =>
    unwrap(api.DELETE("/api/cookies/{cookie_id}", cookiePath(id))),
  );
}

export function useCheckCookieFile() {
  return useMutation({
    mutationFn: ({ id, url }: { id: number; url: string }) =>
      unwrap(api.POST("/api/cookies/{cookie_id}/check", { ...cookiePath(id), body: { url } })),
  });
}
