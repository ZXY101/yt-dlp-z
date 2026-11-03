import { Search } from "lucide-react";
import { type ReactNode, useState } from "react";

import { describeError } from "@/api/errors";
import { CheckboxField } from "@/components/checkbox-field";
import { GroupPicker, GroupTabs } from "@/components/download-options/group-tabs";
import {
  GroupOptions,
  type OptionsProps,
  groupLabel,
} from "@/components/download-options/option-groups";
import {
  type OptionFilter,
  type OptionGroup,
  filterGroups,
} from "@/components/download-options/option-search";
import { FormError } from "@/components/form-error";
import { Input } from "@/components/ui/input";
import { useOptionSchema } from "@/hooks/use-option-schema";

function SearchBox({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <div className="relative md:flex-1">
      <Search
        className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
        aria-hidden
      />
      <Input
        type="search"
        aria-label="Search options"
        placeholder="Search options, e.g. subtitles or --limit-rate"
        className="h-10 pl-9"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

/** Matches from every group at once, so nobody has to guess which tab an option is in. */
function SearchResults({ groups, options, onChange }: OptionsProps & { groups: OptionGroup[] }) {
  if (groups.length === 0) {
    return <p className="p-4 text-sm text-muted-foreground">No options match.</p>;
  }
  return (
    <div className="min-h-0 flex-1 space-y-8 overflow-y-auto p-4">
      {groups.map((group) => (
        <section key={group.title} className="space-y-4">
          <h3 className="text-sm font-medium text-muted-foreground">{groupLabel(group)}</h3>
          <GroupOptions group={group} options={options} onChange={onChange} />
        </section>
      ))}
    </div>
  );
}

function SchemaState({ error }: { error: Error | null }) {
  if (error === null) {
    return <p className="p-4 text-sm text-muted-foreground">Loading yt-dlp options…</p>;
  }
  return (
    <div className="p-4">
      <FormError message={describeError(error)} />
    </div>
  );
}

interface ToolbarProps {
  filter: OptionFilter;
  onFilterChange: (filter: OptionFilter) => void;
  version: string;
  // The group picker (phones only), left out while searching.
  picker: ReactNode;
}

/** Search, group picker and "Only set": two compact rows on phones, one row on wide screens. */
function Toolbar({ filter, onFilterChange, version, picker }: ToolbarProps) {
  return (
    <div className="space-y-2 border-b px-4 py-2 sm:py-3 md:flex md:items-center md:gap-4 md:space-y-0">
      <SearchBox value={filter.query} onChange={(query) => onFilterChange({ ...filter, query })} />
      <div className="flex items-center gap-3">
        {picker}
        <div className="shrink-0 whitespace-nowrap">
          <CheckboxField
            label="Only set"
            checked={filter.onlySet}
            onCheckedChange={(onlySet) => onFilterChange({ ...filter, onlySet })}
          />
        </div>
        <span className="ml-auto hidden truncate text-xs text-muted-foreground sm:inline">
          yt-dlp {version}
        </span>
      </div>
    </div>
  );
}

/** Every yt-dlp option, generated from the installed version's schema. */
export function OptionsEditor({ options, onChange }: OptionsProps) {
  const schema = useOptionSchema();
  const [filter, setFilter] = useState<OptionFilter>({ query: "", onlySet: false });
  const [group, setGroup] = useState<string | null>(null);

  if (!schema.isSuccess) {
    return <SchemaState error={schema.error} />;
  }
  const searching = filter.query.trim() !== "" || filter.onlySet;
  const groups = schema.data.groups;
  const active = group ?? groups[0]?.title ?? "";

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <Toolbar
        filter={filter}
        onFilterChange={setFilter}
        version={schema.data.ytdlp_version}
        picker={
          searching ? null : (
            <GroupPicker
              groups={groups}
              options={options}
              active={active}
              onActiveChange={setGroup}
            />
          )
        }
      />
      {searching ? (
        <SearchResults
          groups={filterGroups(groups, options, filter)}
          options={options}
          onChange={onChange}
        />
      ) : (
        <GroupTabs
          groups={groups}
          options={options}
          onChange={onChange}
          active={active}
          onActiveChange={setGroup}
        />
      )}
    </div>
  );
}
