import type { components } from "@/api/generated/schema";

export type AppSettings = components["schemas"]["AppSettings"];
export type YtdlpInfo = components["schemas"]["YtdlpInfo"];
export type YtdlpChannel = YtdlpInfo["channel"];
export type YtdlpPreferences = components["schemas"]["YtdlpPreferences"];
export type NotificationSettings = components["schemas"]["NotificationSettingsOut"];
export type NotificationSettingsIn = components["schemas"]["NotificationSettingsIn"];
export type NotifyEvent = NotificationSettings["events"][number];
export type PotProviderInfo = components["schemas"]["PotProviderInfo"];
export type ApiToken = components["schemas"]["ApiTokenOut"];
export type ApiTokenCreate = components["schemas"]["ApiTokenCreate"];
export type TokenScope = components["schemas"]["TokenScope"];
