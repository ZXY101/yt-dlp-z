import { SelectField } from "@/components/form-field";
import type { MediaLayout } from "@/lib/download-options";

const CHOICES = [
  { value: "", label: "Off" },
  { value: "season", label: "Folder per channel, season per year" },
  { value: "flat", label: "Folder per channel, no season folders" },
];

interface MediaLayoutFieldProps {
  value: MediaLayout | null;
  onChange: (value: MediaLayout | null) => void;
}

/** Lays downloads out as TV shows for Jellyfin, Plex and Kodi (services/media_server). */
export function MediaLayoutField({ value, onChange }: MediaLayoutFieldProps) {
  return (
    <SelectField
      label="Media server"
      hint="Saves videos as episodes for Jellyfin, Plex or Kodi, e.g. Channel/Season 2026/Channel - S2026E1031 - Title, with a thumbnail and .nfo next to each one. Replaces the file name template."
      value={value ?? ""}
      choices={CHOICES}
      onValueChange={(choice) => onChange(choice ? (choice as MediaLayout) : null)}
    />
  );
}
