import { OptionField } from "@/components/download-options/option-field";
import type { OptionGroup } from "@/components/download-options/option-search";
import { type OptionValues, countSet, setOption } from "@/lib/download-options";

export interface OptionsProps {
  options: OptionValues;
  onChange: (options: OptionValues) => void;
}

/** yt-dlp's group title, without the "Options" most of them end in. */
export function groupLabel(group: OptionGroup) {
  return group.title.replace(/ Options$/, "");
}

export function setInGroup(group: OptionGroup, options: OptionValues) {
  return countSet(
    options,
    group.options.map((option) => option.flag),
  );
}

export function GroupOptions({ group, options, onChange }: OptionsProps & { group: OptionGroup }) {
  return (
    <div className="space-y-4">
      {group.options.map((option) => (
        <OptionField
          key={option.flag}
          option={option}
          value={options[option.flag]}
          onChange={(value) => onChange(setOption(options, option.flag, value))}
        />
      ))}
    </div>
  );
}
