import { CheckboxField } from "@/components/checkbox-field";
import { NumberField } from "@/components/download-options/number-field";
import { SelectField } from "@/components/form-field";
import type { ColourMode, OverlayStyle } from "@/lib/live-chat";

const COLOUR_CHOICES: { value: ColourMode; label: string }[] = [
  { value: "white", label: "White" },
  { value: "random", label: "Random colours" },
  { value: "author", label: "One colour per viewer" },
  { value: "staff", label: "Owner and moderators stand out" },
  { value: "role", label: "Owner, moderators and members stand out" },
];

const PERCENT = 100;

type ShareKey = "opacity" | "screen_area" | "big_share" | "small_share" | "fixed_share";

interface OverlayStyleFieldsProps {
  value: OverlayStyle;
  onChange: (value: OverlayStyle) => void;
}

interface ShareFieldProps extends OverlayStyleFieldsProps {
  name: ShareKey;
  label: string;
  hint?: string;
  min?: number;
}

/** A 0 to 1 share in the API, a percentage in the form. */
function ShareField({ value, onChange, name, label, hint, min = 0 }: ShareFieldProps) {
  return (
    <NumberField
      label={label}
      hint={hint}
      min={min}
      max={PERCENT}
      value={Math.round(value[name] * PERCENT)}
      onChange={(percent) => onChange({ ...value, [name]: percent / PERCENT })}
    />
  );
}

function AmountFields({ value, onChange }: OverlayStyleFieldsProps) {
  return (
    <>
      <NumberField
        label="Most comments on screen"
        hint="Fewer plays more smoothly on phones. Busy moments skip comments, never Super Chats."
        min={1}
        max={200}
        value={value.max_on_screen}
        onChange={(max_on_screen) => onChange({ ...value, max_on_screen })}
      />
      <NumberField
        label="Time on screen (seconds)"
        min={2}
        max={30}
        decimals
        value={value.scroll_seconds}
        onChange={(scroll_seconds) => onChange({ ...value, scroll_seconds })}
      />
      <NumberField
        label="Text size"
        hint="On a 1080p picture."
        min={16}
        max={120}
        value={value.font_size}
        onChange={(font_size) => onChange({ ...value, font_size })}
      />
    </>
  );
}

function VarietyFields(props: OverlayStyleFieldsProps) {
  return (
    <>
      <ShareField {...props} name="big_share" label="Big comments (%)" />
      <ShareField {...props} name="small_share" label="Small comments (%)" />
      <ShareField
        {...props}
        name="fixed_share"
        label="Still comments (%)"
        hint="Held at the top or bottom instead of scrolling."
      />
    </>
  );
}

/** How the scrolling chat looks (backend schemas/live_chat.py OverlayStyle). */
export function OverlayStyleFields(props: OverlayStyleFieldsProps) {
  const { value, onChange } = props;
  return (
    <>
      <SelectField
        label="Comment colours"
        hint="Super Chats always keep their YouTube colour."
        value={value.colour_mode}
        choices={COLOUR_CHOICES}
        onValueChange={(colour_mode) => onChange({ ...value, colour_mode })}
      />
      <AmountFields {...props} />
      <ShareField {...props} name="opacity" label="Opacity (%)" min={10} />
      <ShareField
        {...props}
        name="screen_area"
        label="Screen area (%)"
        hint="How much of the picture comments may use, from the top."
        min={10}
      />
      <NumberField
        label="Timing offset (seconds)"
        hint="Added to every comment. Negative shows chat earlier."
        min={-600}
        max={600}
        decimals
        value={value.offset_seconds}
        onChange={(offset_seconds) => onChange({ ...value, offset_seconds })}
      />
      <VarietyFields {...props} />
      <CheckboxField
        label="Show Super Chats"
        description="In their YouTube colour, with the amount."
        checked={value.show_paid}
        onCheckedChange={(show_paid) => onChange({ ...value, show_paid })}
      />
    </>
  );
}
