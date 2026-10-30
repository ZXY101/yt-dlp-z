/* oxlint-disable jsx-a11y/prefer-tag-over-role -- this is the ARIA combobox pattern. The
   native tag, <datalist>, is what it replaces: Chrome misplaces its popup and can't theme it. */
import { useId, useState } from "react";

import { FieldShell } from "@/components/field-shell";
import { Input } from "@/components/ui/input";
import { parentOf, useFolderSuggestions } from "@/hooks/use-folder-suggestions";
import { useSuggestionList } from "@/hooks/use-suggestion-list";
import { cn } from "@/lib/utils";

interface FolderFieldProps {
  value: string;
  onChange: (value: string) => void;
}

type SuggestionList = ReturnType<typeof useSuggestionList>;

function FolderList({ listId, list }: { listId: string; list: SuggestionList }) {
  return (
    <div
      id={listId}
      role="listbox"
      aria-label="Existing folders"
      hidden={!list.visible}
      className="absolute inset-x-0 top-full z-50 mt-1 max-h-60 overflow-y-auto rounded-lg border bg-popover p-1 text-sm text-popover-foreground shadow-md"
    >
      {list.matches.map((folder, index) => (
        <div
          key={folder}
          id={`${listId}-${index}`}
          role="option"
          tabIndex={-1}
          aria-selected={index === list.active}
          className={cn(
            "cursor-pointer truncate rounded-md px-2 py-2.5 hover:bg-accent",
            index === list.active && "bg-accent text-accent-foreground",
          )}
          // mousedown, not click: picking must happen before the field's blur closes the list.
          onMouseDown={(event) => {
            event.preventDefault();
            list.pick(folder);
          }}
        >
          {folder}
        </div>
      ))}
    </div>
  );
}

/** "Save to", suggesting the server's existing folders as you type.
 * A custom list rather than <datalist>: Chrome misplaces and can't theme the native popup. */
export function FolderField({ value, onChange }: FolderFieldProps) {
  const listId = useId();
  // Only ask the server once the field is used, not on every page load.
  const [used, setUsed] = useState(false);
  const folders = useFolderSuggestions(parentOf(value), used);
  // The trailing slash shows that folder's sub-folders next.
  const list = useSuggestionList({ value, suggestions: folders, onPick: (f) => onChange(`${f}/`) });

  function handleFocus() {
    setUsed(true);
    list.open();
  }

  function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    onChange(event.target.value);
    list.open();
    list.reset();
  }

  return (
    <FieldShell
      label="Save to"
      hint="Leave empty for the default folder. A relative path creates a sub-folder in it."
    >
      {(control) => (
        <div className="relative">
          <Input
            {...control}
            className="h-10"
            placeholder="Default download folder"
            role="combobox"
            aria-autocomplete="list"
            aria-expanded={list.visible}
            aria-controls={listId}
            aria-activedescendant={list.active >= 0 ? `${listId}-${list.active}` : undefined}
            autoComplete="off"
            spellCheck={false}
            value={value}
            onFocus={handleFocus}
            onBlur={list.close}
            onKeyDown={list.handleKeyDown}
            onChange={handleChange}
          />
          <FolderList listId={listId} list={list} />
        </div>
      )}
    </FieldShell>
  );
}
