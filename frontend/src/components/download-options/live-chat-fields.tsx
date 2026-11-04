import { Disclosure } from "@/components/disclosure";
import { OverlayStyleFields } from "@/components/download-options/overlay-style-fields";
import { SelectField } from "@/components/form-field";
import { type LiveChatMode, type LiveChatSettings, overlayStyleOf } from "@/lib/live-chat";

const MODE_CHOICES: { value: LiveChatMode; label: string }[] = [
  { value: "off", label: "Off" },
  { value: "save", label: "Save the chat" },
  { value: "overlay", label: "Save the chat and make an overlay" },
];

const MODE_HINTS: Record<LiveChatMode, string> = {
  off: "For streams: saved while recording, or fetched after a finished stream's video.",
  save: "Saves the chat as a .live_chat.json file next to the video.",
  overlay:
    "Also makes scrolling comments as a .ass subtitle next to the video. Players pick it up by its name, and you can turn it off like any subtitle.",
};

interface LiveChatFieldsProps {
  value: LiveChatSettings;
  onChange: (value: LiveChatSettings) => void;
}

export function LiveChatFields({ value, onChange }: LiveChatFieldsProps) {
  const { mode } = value;
  return (
    <>
      <SelectField
        label="Live chat"
        hint={MODE_HINTS[mode]}
        value={mode}
        choices={MODE_CHOICES}
        onValueChange={(next) => onChange({ ...value, mode: next })}
      />
      {mode === "overlay" && (
        <Disclosure title="Overlay look">
          <OverlayStyleFields
            value={overlayStyleOf(value)}
            onChange={(style) => onChange({ ...style, mode })}
          />
        </Disclosure>
      )}
    </>
  );
}
