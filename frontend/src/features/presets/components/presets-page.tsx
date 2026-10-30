import type { UseQueryResult } from "@tanstack/react-query";
import { Plus, SlidersHorizontal } from "lucide-react";
import { Link } from "react-router";

import { describeError } from "@/api/errors";
import { EmptyState } from "@/components/empty-state";
import { FormError } from "@/components/form-error";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { usePresets } from "@/features/presets/api";
import { PresetCard } from "@/features/presets/components/preset-card";
import type { Preset } from "@/features/presets/types";

function NewPresetButton() {
  return (
    <Button asChild size="lg" className="h-10">
      <Link to="/presets/new">
        <Plus aria-hidden />
        New preset
      </Link>
    </Button>
  );
}

function PresetList({ presets }: { presets: UseQueryResult<Preset[]> }) {
  if (presets.isPending) {
    return <p className="text-sm text-muted-foreground">Loading presets…</p>;
  }
  if (presets.isError) {
    return <FormError message={describeError(presets.error)} />;
  }
  if (presets.data.length === 0) {
    return (
      <EmptyState
        icon={SlidersHorizontal}
        title="No presets yet"
        description="Save options you use often, like audio-only or a channel folder, and pick them when downloading."
      />
    );
  }
  return (
    <ul className="space-y-3" aria-label="Presets">
      {presets.data.map((preset) => (
        <PresetCard key={preset.id} preset={preset} />
      ))}
    </ul>
  );
}

export function PresetsPage() {
  const presets = usePresets();
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader title="Presets" action={<NewPresetButton />} />
      <PresetList presets={presets} />
    </div>
  );
}
