import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";
import type { LoginRequest, PasswordChange, SetupRequest } from "@/features/auth/types";

const AUTH_STATUS_KEY = ["auth", "status"] as const;

export function useAuthStatus() {
  return useQuery({
    queryKey: AUTH_STATUS_KEY,
    queryFn: () => unwrap(api.GET("/api/auth/status")),
  });
}

/** Every auth change (setup, login, logout) is followed by re-reading the status,
 * which lets AuthGate redirect to the right page. */
function useAuthMutation<TBody>(send: (body: TBody) => Promise<unknown>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: send,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: AUTH_STATUS_KEY }),
  });
}

export function useSetup() {
  return useAuthMutation((body: SetupRequest) => unwrap(api.POST("/api/auth/setup", { body })));
}

export function useLogin() {
  return useAuthMutation((body: LoginRequest) => unwrap(api.POST("/api/auth/login", { body })));
}

export function useLogout() {
  return useAuthMutation(() => unwrap(api.POST("/api/auth/logout")));
}

export function useChangePassword() {
  return useAuthMutation((body: PasswordChange) =>
    unwrap(api.POST("/api/auth/password", { body })),
  );
}
