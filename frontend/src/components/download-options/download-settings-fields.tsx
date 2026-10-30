import { Disclosure } from "@/components/disclosure";
import { CommonOptions } from "@/components/download-options/common-options";
import { FolderField } from "@/components/download-options/folder-field";
import { OptionsEditor } from "@/components/download-options/options-editor";
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
      <Disclosure title="Advanced options">
        <FormField
          label="File name template"
          placeholder="%(title)s [%(id)s].%(ext)s"
          hint="A yt-dlp output template. Sub-folders are allowed, e.g. %(uploader)s/%(title)s.%(ext)s."
          value={template}
          onChange={(event) => setOptions(setOption(options, "--output", event.target.value))}
        />
        <Disclosure title="All yt-dlp options" lazy>
          <OptionsEditor options={options} onChange={setOptions} />
        </Disclosure>
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
