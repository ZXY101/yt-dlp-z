import type { components } from "@/api/generated/schema";

export type LiveChatSettings = components["schemas"]["LiveChatSettings"];
export type LiveChatMode = LiveChatSettings["mode"];
export type OverlayStyle = components["schemas"]["OverlayStyle"];
export type ColourMode = OverlayStyle["colour_mode"];

/** The same defaults as the backend's schemas/live_chat.py, to show in the form. */
const DEFAULT_OVERLAY_STYLE: OverlayStyle = {
  scroll_seconds: 7,
  font_size: 48,
  opacity: 0.85,
  screen_area: 0.75,
  max_on_screen: 30,
  offset_seconds: 0,
  show_paid: true,
  colour_mode: "white",
  big_share: 0,
  small_share: 0,
  fixed_share: 0,
};

export const CHAT_OFF: LiveChatSettings = { mode: "off", ...DEFAULT_OVERLAY_STYLE };

/** A saved job's or preset's look, or the defaults when it has none. */
export function overlayStyleOf(settings: LiveChatSettings | null | undefined): OverlayStyle {
  if (!settings) {
    return DEFAULT_OVERLAY_STYLE;
  }
  const { mode: _mode, ...style } = settings;
  return style;
}
