import type { components } from "@/api/generated/schema";
import { type OptionValues, isOn } from "@/lib/download-options";

export type OptionGroup = components["schemas"]["OptionGroup"];
export type OptionSpec = components["schemas"]["OptionSpec"];

export interface OptionFilter {
  query: string;
  onlySet: boolean;
}

function matches(option: OptionSpec, query: string) {
  const text = [option.flag, ...option.aliases, ...option.short, option.help].join(" ");
  return text.toLowerCase().includes(query);
}

/** Groups with only the options that match the search; empty groups are dropped. */
export function filterGroups(
  groups: OptionGroup[],
  options: OptionValues,
  filter: OptionFilter,
): OptionGroup[] {
  const query = filter.query.trim().toLowerCase();
  return groups
    .map((group) => ({
      ...group,
      options: group.options.filter((option) => {
        const shown = !filter.onlySet || isOn(options, option.flag);
        return shown && (!query || matches(option, query));
      }),
    }))
    .filter((group) => group.options.length > 0);
}
