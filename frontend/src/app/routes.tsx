import type { RouteObject } from "react-router";

import { AppLayout } from "@/app/layout/app-layout";
import { AuthGate } from "@/features/auth/components/auth-gate";
import { LoginPage } from "@/features/auth/components/login-page";
import { SetupPage } from "@/features/auth/components/setup-page";
import { CookiesPage } from "@/features/cookies";
import { DownloadPage, QueuePage } from "@/features/downloads";
import { PresetEditorPage, PresetsPage } from "@/features/presets";
import { SettingsPage } from "@/features/settings";
import { SubscriptionEditorPage, SubscriptionsPage } from "@/features/subscriptions";

export const routes: RouteObject[] = [
  {
    element: <AuthGate />,
    children: [
      { path: "/setup", element: <SetupPage /> },
      { path: "/login", element: <LoginPage /> },
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <DownloadPage /> },
          { path: "/queue", element: <QueuePage /> },
          { path: "/subscriptions", element: <SubscriptionsPage /> },
          { path: "/subscriptions/new", element: <SubscriptionEditorPage /> },
          { path: "/subscriptions/:subscriptionId", element: <SubscriptionEditorPage /> },
          { path: "/presets", element: <PresetsPage /> },
          { path: "/presets/new", element: <PresetEditorPage /> },
          { path: "/presets/:presetId", element: <PresetEditorPage /> },
          { path: "/cookies", element: <CookiesPage /> },
          { path: "/settings", element: <SettingsPage /> },
        ],
      },
    ],
  },
];
