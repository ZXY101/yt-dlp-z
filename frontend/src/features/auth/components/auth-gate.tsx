import { Navigate, Outlet, useLocation } from "react-router";

import { describeError } from "@/api/errors";
import { ErrorScreen, LoadingScreen } from "@/components/page-status";
import { useAuthStatus } from "@/features/auth/api";
import { authRedirect } from "@/features/auth/auth-redirect";

export function AuthGate() {
  const { pathname } = useLocation();
  const status = useAuthStatus();

  if (status.isPending) {
    return <LoadingScreen />;
  }
  if (status.isError) {
    return (
      <ErrorScreen message={describeError(status.error)} onRetry={() => void status.refetch()} />
    );
  }

  const redirectTo = authRedirect(status.data, pathname);
  if (redirectTo) {
    return <Navigate to={redirectTo} replace />;
  }
  return <Outlet />;
}
