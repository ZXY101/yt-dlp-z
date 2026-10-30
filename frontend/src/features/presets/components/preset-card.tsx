import { Pencil, Trash2 } from "lucide-react";
import { Link } from "react-router";

import { describeError } from "@/api/errors";
import { ConfirmButton } from "@/components/confirm-button";
import { FormError } from "@/components/form-error";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useDeletePreset } from "@/features/presets/api";
import type { Preset } from "@/features/presets/types";

function describePreset(preset: Preset) {
  const optionCount = Object.keys(preset.options ?? {}).length;
  const parts = [
    preset.output_dir ? `Saves to ${preset.output_dir}` : "Default folder",
    optionCount === 1 ? "1 option" : `${optionCount} options`,
  ];
  if (preset.extra_args) {
    parts.push("extra options");
  }
  if (preset.cookie_id !== null) {
    parts.push("with cookies");
  }
  return parts.join(" · ");
}

export function PresetCard({ preset }: { preset: Preset }) {
  const remove = useDeletePreset();
  return (
    <li className="space-y-3 rounded-xl border p-4">
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1 space-y-1">
          <p className="truncate font-medium">{preset.name}</p>
          <p className="text-xs break-words text-muted-foreground">{describePreset(preset)}</p>
        </div>
        {preset.is_default && <Badge variant="secondary">Default</Badge>}
      </div>
      <FormError message={remove.isError ? describeError(remove.error) : null} />
      <div className="flex flex-wrap justify-end gap-2">
        <Button asChild variant="ghost" className="h-10">
          <Link to={`/presets/${preset.id}`} aria-label={`Edit ${preset.name}`}>
            <Pencil aria-hidden />
            Edit
          </Link>
        </Button>
        <ConfirmButton
          trigger={
            <Button variant="ghost" className="h-10" aria-label={`Delete ${preset.name}`}>
              <Trash2 aria-hidden />
              Delete
            </Button>
          }
          title={`Delete ${preset.name}?`}
          description="Downloads already started keep their options. This can't be undone."
          confirmText="Delete"
          onConfirm={() => remove.mutate(preset.id)}
        />
      </div>
    </li>
  );
}
