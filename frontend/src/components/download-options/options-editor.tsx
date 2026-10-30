import { Search } from "lucide-react";
import { useState } from "react";

import { describeError } from "@/api/errors";
import { CheckboxField } from "@/components/checkbox-field";
import { GroupTabs } from "@/components/download-options/group-tabs";
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
    <div className="relative">
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

/** Every yt-dlp option, generated from the installed version's schema. */
export function OptionsEditor({ options, onChange }: OptionsProps) {
  const schema = useOptionSchema();
  const [filter, setFilter] = useState<OptionFilter>({ query: "", onlySet: false });

  if (schema.isPending) {
    return <p className="p-4 text-sm text-muted-foreground">Loading yt-dlp options…</p>;
  }
  if (schema.isError) {
    return (
      <div className="p-4">
        <FormError message={describeError(schema.error)} />
      </div>
    );
  }
  const searching = filter.query.trim() !== "" || filter.onlySet;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="space-y-2 border-b px-4 pt-3 pb-2">
        <SearchBox value={filter.query} onChange={(query) => setFilter({ ...filter, query })} />
        <div className="flex items-center justify-between gap-3">
          <CheckboxField
            label="Only options that are set"
            checked={filter.onlySet}
            onCheckedChange={(onlySet) => setFilter({ ...filter, onlySet })}
          />
          <span className="text-xs text-muted-foreground">yt-dlp {schema.data.ytdlp_version}</span>
        </div>
      </div>
      {searching ? (
        <SearchResults
          groups={filterGroups(schema.data.groups, options, filter)}
          options={options}
          onChange={onChange}
        />
      ) : (
        <GroupTabs groups={schema.data.groups} options={options} onChange={onChange} />
      )}
    </div>
  );
}
