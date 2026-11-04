export type Theme = "light" | "dark";

const DARK_QUERY = "(prefers-color-scheme: dark)";
// index.html reads this key too, to set the theme before the first paint.
const STORAGE_KEY = "yt-dlp-z-theme";

const listeners = new Set<() => void>();
let preference: Theme | null = null;

function systemTheme(): Theme {
  return window.matchMedia(DARK_QUERY).matches ? "dark" : "light";
}

function readPreference(): Theme | null {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : null;
  } catch {
    return null;
  }
}

function writePreference(theme: Theme | null) {
  try {
    if (theme) {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // Storage can be blocked. The choice then lasts until the page reloads.
  }
}

export function getTheme(): Theme {
  return preference ?? systemTheme();
}

function applyTheme() {
  document.documentElement.classList.toggle("dark", getTheme() === "dark");
  for (const listener of listeners) {
    listener();
  }
}

function reloadPreference() {
  preference = readPreference();
  applyTheme();
}

export function initTheme() {
  reloadPreference();
  window.matchMedia(DARK_QUERY).addEventListener("change", applyTheme);
  // Fires when another tab changes the theme.
  window.addEventListener("storage", reloadPreference);
}

export function toggleTheme() {
  const next: Theme = getTheme() === "dark" ? "light" : "dark";
  // Picking the look the system already has means following the system again.
  preference = next === systemTheme() ? null : next;
  writePreference(preference);
  applyTheme();
}

export function subscribeToTheme(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
