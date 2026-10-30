import { Search } from "lucide-react";
import { useState } from "react";

import { describeError } from "@/api/errors";
import { CheckboxField } from "@/components/checkbox-field";
import { Disclosure } from "@/components/disclosure";
import { OptionField } from "@/components/download-options/option-field";
import {
  type OptionFilter,
  type OptionGroup,
  filterGroups,
} from "@/components/download-options/option-search";
import { FormError } from "@/components/form-error";
import { Input } from "@/components/ui/input";
import { useOptionSchema } from "@/hooks/use-option-schema";
import { type OptionValues, countSet, setOption } from "@/lib/download-options";

interface OptionsEditorProps {
  options: OptionValues;
  onChange: (options: OptionValues) => void;
}

function GroupSection({
  group,
  options,
  onChange,
  searching,
}: OptionsEditorProps & { group: OptionGroup; searching: boolean }) {
  const flags = group.options.map((option) => option.flag);
  const setCount = countSet(options, flags);
  return (
    <Disclosure
      title={group.title}
      summary={setCount > 0 ? `${setCount} set` : undefined}
      forceOpen={searching ? true : undefined}
      lazy
    >
      <div className="space-y-4 border-l pl-4">
        {group.options.map((option) => (
          <OptionField
            key={option.flag}
            option={option}
            value={options[option.flag]}
            onChange={(value) => onChange(setOption(options, option.flag, value))}
          />
        ))}
      </div>
    </Disclosure>
  );
}

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

/** Every yt-dlp option, generated from the installed version's schema. */
export function OptionsEditor({ options, onChange }: OptionsEditorProps) {
  const schema = useOptionSchema();
  const [filter, setFilter] = useState<OptionFilter>({ query: "", onlySet: false });

  if (schema.isPending) {
    return <p className="text-sm text-muted-foreground">Loading yt-dlp options…</p>;
  }
  if (schema.isError) {
    return <FormError message={describeError(schema.error)} />;
  }
  const groups = filterGroups(schema.data.groups, options, filter);
  const searching = filter.query.trim() !== "" || filter.onlySet;

  return (
    <div className="space-y-3">
      <SearchBox value={filter.query} onChange={(query) => setFilter({ ...filter, query })} />
      <CheckboxField
        label="Only options that are set"
        checked={filter.onlySet}
        onCheckedChange={(onlySet) => setFilter({ ...filter, onlySet })}
      />
      {groups.length === 0 && <p className="text-sm text-muted-foreground">No options match.</p>}
      {groups.map((group) => (
        <GroupSection
          key={group.title}
          group={group}
          options={options}
          onChange={onChange}
          searching={searching}
        />
      ))}
      <p className="text-xs text-muted-foreground">yt-dlp {schema.data.ytdlp_version}</p>
    </div>
  );
}
