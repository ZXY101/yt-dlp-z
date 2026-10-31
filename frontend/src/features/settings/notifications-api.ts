import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";
import type { NotificationSettingsIn } from "@/features/settings/types";

const NOTIFICATIONS_KEY = ["notifications"];

export function useNotificationSettings() {
  return useQuery({
    queryKey: NOTIFICATIONS_KEY,
    queryFn: () => unwrap(api.GET("/api/notifications")),
  });
}

export function useSaveNotifications() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: NotificationSettingsIn) => unwrap(api.PUT("/api/notifications", { body })),
    onSuccess: (saved) => queryClient.setQueryData(NOTIFICATIONS_KEY, saved),
  });
}

/** Sends a test message with the settings as typed, saved or not. */
export function useTestNotification() {
  return useMutation({
    mutationFn: (body: NotificationSettingsIn) =>
      unwrap(api.POST("/api/notifications/test", { body })),
  });
}
