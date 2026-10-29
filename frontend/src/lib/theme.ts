const DARK_QUERY = "(prefers-color-scheme: dark)";

export function applySystemTheme() {
  const media = window.matchMedia(DARK_QUERY);

  function sync() {
    document.documentElement.classList.toggle("dark", media.matches);
  }

  sync();
  media.addEventListener("change", sync);
}
