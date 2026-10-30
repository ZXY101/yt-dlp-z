import { ArrowRight, type LucideIcon } from "lucide-react";
import { Link } from "react-router";

/** What clicking the empty state does: open a page, or act on this one. */
type EmptyStateAction = { label: string } & ({ to: string } | { onClick: () => void });

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action: EmptyStateAction;
}

const BOX_CLASSES =
  "group flex w-full flex-col items-center gap-3 rounded-xl border border-dashed p-10 text-center " +
  "cursor-pointer transition-colors hover:border-foreground/30 hover:bg-muted/50 " +
  "outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50";

/** The whole box is the call to action, so the first step is one click away. */
export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  const content = (
    <>
      <Icon className="size-8 text-muted-foreground" aria-hidden />
      <span className="font-medium">{title}</span>
      <span className="max-w-sm text-sm text-muted-foreground">{description}</span>
      <span className="inline-flex items-center gap-1 text-sm font-medium group-hover:underline">
        {action.label}
        <ArrowRight className="size-4" aria-hidden />
      </span>
    </>
  );
  if ("to" in action) {
    return (
      <Link to={action.to} className={BOX_CLASSES}>
        {content}
      </Link>
    );
  }
  return (
    <button type="button" className={BOX_CLASSES} onClick={action.onClick}>
      {content}
    </button>
  );
}
