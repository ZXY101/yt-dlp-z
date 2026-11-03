import { CheckboxField } from "@/components/checkbox-field";
import { SelectField } from "@/components/form-field";
import type { DownloadSettings, FileNaming, FolderLayout } from "@/lib/download-options";

const FOLDER_CHOICES = [
  { value: "", label: "None, straight into the folder" },
  { value: "channel", label: "Channel" },
  { value: "season", label: "Channel / Season 2026" },
];

const NAME_CHOICES = [
  { value: "", label: "yt-dlp default, or the template below" },
  { value: "title_id", label: "Title [id]" },
  { value: "dated", label: "[20261103] Title" },
  { value: "dated_id", label: "[20261103] Title [id]" },
  { value: "episode", label: "Channel - S2026E1103 - Title [id]" },
];

type Layout = Pick<DownloadSettings, "folders" | "fileName" | "mediaFiles">;

interface LayoutFieldsProps {
  value: Layout;
  onChange: (value: Layout) => void;
}

/** Folders, file names and media-server files (backend services/media_server/layout.py). */
export function LayoutFields({ value, onChange }: LayoutFieldsProps) {
  return (
    <>
      <SelectField
        label="Sub-folders"
        hint="Inside the download folder. Season folders are named after the year it aired."
        value={value.folders ?? ""}
        choices={FOLDER_CHOICES}
        onValueChange={(choice) =>
          onChange({ ...value, folders: choice ? (choice as FolderLayout) : null })
        }
      />
      <SelectField
        label="File name"
        hint="Dates are the day it aired (a stream's start, not when its waiting room was made). Channel - S2026E1103 suits Jellyfin, Plex and Kodi TV libraries."
        value={value.fileName ?? ""}
        choices={NAME_CHOICES}
        onValueChange={(choice) =>
          onChange({ ...value, fileName: choice ? (choice as FileNaming) : null })
        }
      />
      <CheckboxField
        label="Media-server files"
        description="A thumbnail and .nfo next to each video, and the channel's tvshow.nfo and artwork, for Jellyfin, Plex and Kodi."
        checked={value.mediaFiles}
        onCheckedChange={(mediaFiles) => onChange({ ...value, mediaFiles })}
      />
    </>
  );
}
