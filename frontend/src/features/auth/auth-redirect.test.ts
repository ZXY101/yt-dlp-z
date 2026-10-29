import { authRedirect } from "@/features/auth/auth-redirect";
import type { AuthStatus } from "@/features/auth/types";

function status(overrides: Partial<AuthStatus>): AuthStatus {
  return {
    setup_required: false,
    authenticated: true,
    auth_mode: "password",
    default_download_dir: "/downloads",
    ...overrides,
  };
}

describe("authRedirect", () => {
  it.each([
    ["setup required, elsewhere", status({ setup_required: true }), "/", "/setup"],
    ["setup required, on setup", status({ setup_required: true }), "/setup", null],
    ["signed out, elsewhere", status({ authenticated: false }), "/", "/login"],
    ["signed out, on login", status({ authenticated: false }), "/login", null],
    ["signed in, on login", status({}), "/login", "/"],
    ["signed in, on setup", status({}), "/setup", "/"],
    ["signed in, in the app", status({}), "/", null],
  ])("%s", (_name, authStatus, pathname, expected) => {
    expect(authRedirect(authStatus, pathname)).toBe(expected);
  });
});
