import type { AuthStatus } from "@/features/auth/types";

const SETUP_PATH = "/setup";
const LOGIN_PATH = "/login";
const HOME_PATH = "/";

/** Where the user should be sent for a given auth status, or null to stay put. */
export function authRedirect(status: AuthStatus, pathname: string): string | null {
  const onSetup = pathname === SETUP_PATH;
  const onLogin = pathname === LOGIN_PATH;

  if (status.setup_required) {
    return onSetup ? null : SETUP_PATH;
  }
  if (!status.authenticated) {
    return onLogin ? null : LOGIN_PATH;
  }
  if (onSetup || onLogin) {
    return HOME_PATH;
  }
  return null;
}
