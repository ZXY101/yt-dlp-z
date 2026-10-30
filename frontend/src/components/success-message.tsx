import { CircleCheck } from "lucide-react";

/** A polite status message (announced without interrupting), e.g. after saving. */
export function SuccessMessage({ children }: { children: React.ReactNode }) {
  return (
    <output className="flex items-start gap-2.5 rounded-lg border px-4 py-3 text-sm">
      <CircleCheck className="mt-0.5 size-4 shrink-0" aria-hidden />
      <span>{children}</span>
    </output>
  );
}
