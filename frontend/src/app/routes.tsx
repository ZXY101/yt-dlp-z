import type { RouteObject } from "react-router";

import { AppLayout } from "@/app/layout/app-layout";
import { AuthGate } from "@/features/auth/components/auth-gate";
import { LoginPage } from "@/features/auth/components/login-page";
import { SetupPage } from "@/features/auth/components/setup-page";
import { DashboardPage } from "@/features/dashboard/components/dashboard-page";
import { DownloadPage, QueuePage } from "@/features/downloads";

export const routes: RouteObject[] = [
  {
    element: <AuthGate />,
    children: [
      { path: "/setup", element: <SetupPage /> },
      { path: "/login", element: <LoginPage /> },
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: "/download", element: <DownloadPage /> },
          { path: "/queue", element: <QueuePage /> },
        ],
      },
    ],
  },
];
