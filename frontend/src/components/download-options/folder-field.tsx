import { useId, useState } from "react";

import { FormField } from "@/components/form-field";
import { parentOf, useFolderSuggestions } from "@/hooks/use-folder-suggestions";

interface FolderFieldProps {
  value: string;
  onChange: (value: string) => void;
}

/** "Save to", suggesting the server's existing folders as you type. */
export function FolderField({ value, onChange }: FolderFieldProps) {
  const listId = useId();
  // Only ask the server once the field is used, not on every page load.
  const [focused, setFocused] = useState(false);
  const folders = useFolderSuggestions(parentOf(value), focused);

  return (
    <>
      <FormField
        label="Save to"
        placeholder="Default download folder"
        hint="Leave empty for the default folder. A relative path creates a sub-folder in it."
        list={listId}
        autoComplete="off"
        spellCheck={false}
        value={value}
        onFocus={() => setFocused(true)}
        onChange={(event) => onChange(event.target.value)}
      />
      <datalist id={listId}>
        {folders.map((folder) => (
          <option key={folder} value={folder}>
            {folder}
          </option>
        ))}
      </datalist>
    </>
  );
}
