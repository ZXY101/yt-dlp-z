import { useSyncExternalStore } from "react";

import { getTheme, subscribeToTheme } from "@/lib/theme";

export function useTheme() {
  return useSyncExternalStore(subscribeToTheme, getTheme);
}
