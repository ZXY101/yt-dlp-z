import type { components } from "@/api/generated/schema";

export type AppSettings = components["schemas"]["AppSettings"];
export type YtdlpInfo = components["schemas"]["YtdlpInfo"];
export type YtdlpChannel = YtdlpInfo["channel"];
export type YtdlpPreferences = components["schemas"]["YtdlpPreferences"];
export type NotificationSettings = components["schemas"]["NotificationSettingsOut"];
export type NotificationSettingsIn = components["schemas"]["NotificationSettingsIn"];
export type NotifyEvent = NotificationSettings["events"][number];
