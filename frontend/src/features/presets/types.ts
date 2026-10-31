import type { components } from "@/api/generated/schema";

export type Preset = components["schemas"]["PresetOut"];
export type PresetIn = components["schemas"]["PresetIn"];
export type PresetKind = Preset["kind"];
export type RecordingSettings = components["schemas"]["RecordingSettings"];
