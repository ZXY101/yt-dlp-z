import { Pencil, Trash2 } from "lucide-react";
import { Link } from "react-router";

import { describeError } from "@/api/errors";
import { ConfirmButton } from "@/components/confirm-button";
import { FormError } from "@/components/form-error";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useDeletePreset } from "@/features/presets/api";
import { PRESET_KIND_LABELS } from "@/features/presets/kinds";
import type { Preset, RecordingSettings } from "@/features/presets/types";

function hours(count: number) {
  return count === 1 ? "1 hour" : `${count} hours`;
}

/** e.g. "New file every 6 hours · until the stream ends" */
function describeRecording(recording: RecordingSettings) {
  const parts = [
    recording.part_hours ? `New file every ${hours(recording.part_hours)}` : "One file",
    recording.max_hours ? `stops after ${hours(recording.max_hours)}` : "until the stream ends",
  ];
  return parts.join(" · ");
}

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
  if (preset.recording) {
    parts.push(describeRecording(preset.recording).toLowerCase());
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
        <div className="flex shrink-0 flex-wrap justify-end gap-1">
          {preset.kind !== "any" && (
            <Badge variant="outline">{PRESET_KIND_LABELS[preset.kind]}</Badge>
          )}
          {preset.is_default && <Badge variant="secondary">Default</Badge>}
        </div>
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
