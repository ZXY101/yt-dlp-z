import { Disclosure } from "@/components/disclosure";
import { CommonOptions } from "@/components/download-options/common-options";
import { FolderField } from "@/components/download-options/folder-field";
import { LayoutFields } from "@/components/download-options/layout-fields";
import { OptionsDialog } from "@/components/download-options/options-dialog";
import { ProxyField } from "@/components/download-options/proxy-field";
import { FormField, SelectField, TextareaField } from "@/components/form-field";
import { type DownloadSettings, setOption } from "@/lib/download-options";

interface CookieChoice {
  id: number;
  name: string;
}

interface DownloadSettingsFieldsProps {
  value: DownloadSettings;
  onChange: (value: DownloadSettings) => void;
  cookieFiles: CookieChoice[];
  proxyCount: number;
}

function CookiesField({ value, onChange, cookieFiles }: DownloadSettingsFieldsProps) {
  if (cookieFiles.length === 0) {
    return null;
  }
  const choices = [
    { value: "", label: "None" },
    ...cookieFiles.map((file) => ({ value: String(file.id), label: file.name })),
  ];
  return (
    <SelectField
      label="Cookies"
      hint="Signs in to the site, for members-only or age-restricted videos."
      value={value.cookieId === null ? "" : String(value.cookieId)}
      choices={choices}
      onValueChange={(id) => onChange({ ...value, cookieId: id ? Number(id) : null })}
    />
  );
}

function templateHint({ fileName, folders }: DownloadSettings): string {
  if (fileName) {
    return "Not used: File name above names the files.";
  }
  if (folders) {
    return "A yt-dlp output template, used inside the sub-folders chosen above.";
  }
  return "A yt-dlp output template. Sub-folders are allowed, e.g. %(uploader)s/%(title)s.%(ext)s.";
}

/** Folder, cookies and yt-dlp options: everything a download or preset needs besides a URL. */
export function DownloadSettingsFields(props: DownloadSettingsFieldsProps) {
  const { value, onChange } = props;
  const options = value.options;
  const template = typeof options["--output"] === "string" ? options["--output"] : "";

  function setOptions(next: DownloadSettings["options"]) {
    onChange({ ...value, options: next });
  }

  return (
    <>
      <FolderField
        value={value.outputDir}
        onChange={(outputDir) => onChange({ ...value, outputDir })}
      />
      <CookiesField {...props} />
      <CommonOptions options={options} onChange={setOptions} />
      <LayoutFields value={value} onChange={(layout) => onChange({ ...value, ...layout })} />
      <ProxyField
        value={value.proxyMode}
        proxyCount={props.proxyCount}
        onChange={(proxyMode) => onChange({ ...value, proxyMode })}
      />
      <Disclosure title="Advanced options">
        <FormField
          label="File name template"
          placeholder="%(title)s [%(id)s].%(ext)s"
          hint={templateHint(value)}
          value={template}
          onChange={(event) => setOptions(setOption(options, "--output", event.target.value))}
        />
        <OptionsDialog options={options} onChange={setOptions} />
        <TextareaField
          label="Extra yt-dlp options"
          placeholder="--limit-rate 2M --embed-chapters"
          hint="Any yt-dlp command-line options. Options that run programs or use files outside the download folder are blocked."
          spellCheck={false}
          value={value.extraArgs}
          onChange={(event) => onChange({ ...value, extraArgs: event.target.value })}
        />
      </Disclosure>
    </>
  );
}
