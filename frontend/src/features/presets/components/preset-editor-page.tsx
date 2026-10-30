import { Link, useParams } from "react-router";

import { describeError } from "@/api/errors";
import { CheckboxField } from "@/components/checkbox-field";
import { DownloadSettingsFields } from "@/components/download-options/download-settings-fields";
import { FormError } from "@/components/form-error";
import { FormField } from "@/components/form-field";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { useCookieFiles } from "@/features/cookies";
import { usePresets } from "@/features/presets/api";
import { usePresetForm } from "@/features/presets/hooks/use-preset-form";
import type { Preset } from "@/features/presets/types";

function PresetForm({ preset }: { preset: Preset | null }) {
  const form = usePresetForm(preset);
  const cookieFiles = useCookieFiles().data ?? [];

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    form.submit();
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit} noValidate>
      <FormError message={form.save.isError ? describeError(form.save.error) : null} />
      <FormField
        label="Name"
        placeholder="Music"
        value={form.fields.name}
        error={form.nameError}
        onChange={(event) => form.setters.setName(event.target.value)}
      />
      <CheckboxField
        label="Use by default"
        description="Picked automatically on the download page."
        checked={form.fields.isDefault}
        onCheckedChange={form.setters.setIsDefault}
      />
      <DownloadSettingsFields
        value={form.fields.settings}
        onChange={form.setters.setSettings}
        cookieFiles={cookieFiles}
      />
      <div className="flex flex-wrap gap-2">
        <Button type="submit" size="lg" className="h-10" disabled={form.save.isPending}>
          {form.save.isPending ? "Saving…" : "Save preset"}
        </Button>
        <Button asChild variant="ghost" size="lg" className="h-10">
          <Link to="/presets">Cancel</Link>
        </Button>
      </div>
    </form>
  );
}

function EditorContent({ presetId }: { presetId: number | null }) {
  const presets = usePresets();
  if (presetId === null) {
    return <PresetForm preset={null} />;
  }
  if (presets.isPending) {
    return <p className="text-sm text-muted-foreground">Loading preset…</p>;
  }
  if (presets.isError) {
    return <FormError message={describeError(presets.error)} />;
  }
  const preset = presets.data.find((item) => item.id === presetId);
  if (!preset) {
    return <FormError message="This preset doesn't exist any more." />;
  }
  return <PresetForm key={preset.id} preset={preset} />;
}

export function PresetEditorPage() {
  const { presetId } = useParams();
  const id = presetId === undefined ? null : Number(presetId);
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader title={id === null ? "New preset" : "Edit preset"} />
      <EditorContent presetId={id} />
    </div>
  );
}
