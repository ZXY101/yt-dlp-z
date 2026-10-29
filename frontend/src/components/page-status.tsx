import { LoaderCircle, TriangleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";

export function LoadingScreen() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <output>
        <LoaderCircle className="size-6 animate-spin text-muted-foreground" aria-hidden />
        <span className="sr-only">Loading</span>
      </output>
    </div>
  );
}

interface ErrorScreenProps {
  message: string;
  onRetry: () => void;
}

export function ErrorScreen({ message, onRetry }: ErrorScreenProps) {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4 p-4 text-center">
      <TriangleAlert className="size-8 text-destructive" aria-hidden />
      <div className="space-y-1">
        <h1 className="text-lg font-semibold">Can't reach the server</h1>
        <p className="text-sm text-muted-foreground">{message}</p>
      </div>
      <Button size="lg" onClick={onRetry}>
        Try again
      </Button>
    </div>
  );
}
