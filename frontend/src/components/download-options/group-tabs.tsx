import { Tabs } from "radix-ui";
import { useState } from "react";

import {
  GroupOptions,
  type OptionsProps,
  groupLabel,
  setInGroup,
} from "@/components/download-options/option-groups";
import type { OptionGroup } from "@/components/download-options/option-search";
import { SelectField } from "@/components/form-field";

interface GroupTabsProps extends OptionsProps {
  groups: OptionGroup[];
}

function choiceLabel(group: OptionGroup, setCount: number) {
  return setCount > 0 ? `${groupLabel(group)} (${setCount} set)` : groupLabel(group);
}

/** One tab per yt-dlp option group: a list down the side on wide screens, a picker on phones. */
export function GroupTabs({ groups, options, onChange }: GroupTabsProps) {
  const [active, setActive] = useState(groups[0]?.title ?? "");
  const counts = new Map(groups.map((group) => [group.title, setInGroup(group, options)]));
  const choices = groups.map((group) => ({
    value: group.title,
    label: choiceLabel(group, counts.get(group.title) ?? 0),
  }));

  return (
    <Tabs.Root
      value={active}
      onValueChange={setActive}
      orientation="vertical"
      className="flex min-h-0 flex-1 flex-col md:flex-row"
    >
      <div className="border-b px-4 py-3 md:hidden">
        <SelectField
          label="Option group"
          value={active}
          choices={choices}
          onValueChange={setActive}
        />
      </div>
      <Tabs.List
        aria-label="Option groups"
        className="hidden w-60 shrink-0 space-y-0.5 overflow-y-auto border-r p-2 md:block"
      >
        {groups.map((group) => (
          <GroupTab key={group.title} group={group} setCount={counts.get(group.title) ?? 0} />
        ))}
      </Tabs.List>
      {groups.map((group) => (
        <Tabs.Content
          key={group.title}
          value={group.title}
          className="min-h-0 flex-1 overflow-y-auto p-4 outline-none"
        >
          <GroupOptions group={group} options={options} onChange={onChange} />
        </Tabs.Content>
      ))}
    </Tabs.Root>
  );
}

function GroupTab({ group, setCount }: { group: OptionGroup; setCount: number }) {
  return (
    <Tabs.Trigger
      value={group.title}
      aria-label={setCount > 0 ? `${groupLabel(group)}, ${setCount} set` : undefined}
      className="flex min-h-9 w-full cursor-pointer items-center justify-between gap-2 rounded-md px-3 py-1.5 text-left text-sm hover:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none data-[state=active]:bg-muted data-[state=active]:font-medium"
    >
      {groupLabel(group)}
      {setCount > 0 && (
        <span className="rounded-full bg-primary px-1.5 text-xs font-medium text-primary-foreground tabular-nums">
          {setCount}
        </span>
      )}
    </Tabs.Trigger>
  );
}
