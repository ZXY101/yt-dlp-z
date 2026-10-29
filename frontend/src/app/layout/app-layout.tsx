import { Download, LogOut } from "lucide-react";
import { Outlet } from "react-router";

import { MobileNav } from "@/app/layout/mobile-nav";
import { NavLinks } from "@/app/layout/nav-links";
import { Button } from "@/components/ui/button";
import { useAuthStatus, useLogout } from "@/features/auth/api";

function LogoutButton() {
  const logout = useLogout();
  return (
    <Button
      variant="ghost"
      size="lg"
      className="h-10"
      disabled={logout.isPending}
      onClick={() => logout.mutate(undefined)}
    >
      <LogOut aria-hidden />
      Sign out
    </Button>
  );
}

export function AppLayout() {
  const { data: status } = useAuthStatus();
  const showLogout = status?.auth_mode === "password";

  return (
    <div className="flex min-h-svh flex-col">
      <header className="flex h-14 items-center gap-2 border-b px-4">
        <MobileNav />
        <div className="flex items-center gap-2 font-semibold">
          <Download className="size-5" aria-hidden />
          yt-dlp-z
        </div>
        <div className="ml-auto">{showLogout && <LogoutButton />}</div>
      </header>
      <div className="flex flex-1">
        <aside className="hidden w-56 shrink-0 border-r p-3 md:block">
          <NavLinks />
        </aside>
        <main className="min-w-0 flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
