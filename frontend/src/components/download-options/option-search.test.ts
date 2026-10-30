import { type OptionGroup, filterGroups } from "@/components/download-options/option-search";

function option(flag: string, help: string, aliases: string[] = []) {
  return {
    flag,
    aliases,
    short: [],
    kind: "flag" as const,
    repeatable: false,
    metavar: null,
    choices: null,
    help,
  };
}

const groups: OptionGroup[] = [
  {
    title: "Network",
    options: [option("--proxy", "Use the HTTP proxy"), option("--ipv4", "IPv4")],
  },
  { title: "Subtitles", options: [option("--write-subs", "Write subtitle file", ["--srt"])] },
];

function titles(query: string) {
  return filterGroups(groups, {}, { query, onlySet: false }).map((group) => [
    group.title,
    group.options.map((item) => item.flag),
  ]);
}

describe("filterGroups", () => {
  it("keeps everything without a filter", () => {
    expect(filterGroups(groups, {}, { query: "", onlySet: false })).toEqual(groups);
  });

  it("searches flags, aliases and help text, ignoring case", () => {
    expect(titles("PROXY")).toEqual([["Network", ["--proxy"]]]);
    expect(titles("--srt")).toEqual([["Subtitles", ["--write-subs"]]]);
    expect(titles("nothing like this")).toEqual([]);
  });

  it("can show only the options that are set", () => {
    const result = filterGroups(groups, { "--ipv4": true }, { query: "", onlySet: true });
    expect(result).toEqual([{ title: "Network", options: [groups[0]!.options[1]] }]);
  });
});
