import { Inbox } from "lucide-react";

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed p-10 text-center">
        <Inbox className="size-8 text-muted-foreground" aria-hidden />
        <p className="font-medium">Nothing here yet</p>
        <p className="max-w-sm text-sm text-muted-foreground">
          Downloads, channel subscriptions and live recordings will show up here.
        </p>
      </div>
    </div>
  );
}
