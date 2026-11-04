import { getTheme, initTheme, subscribeToTheme, toggleTheme } from "@/lib/theme";

const STORAGE_KEY = "yt-dlp-z-theme";

function stubSystemTheme(initiallyDark: boolean) {
  const captured: { onChange?: () => void } = {};
  const media = {
    matches: initiallyDark,
    addEventListener(_event: string, callback: () => void) {
      captured.onChange = callback;
    },
  };
  vi.stubGlobal("matchMedia", () => media);
  return {
    change(dark: boolean) {
      media.matches = dark;
      captured.onChange?.();
    },
  };
}

function isDark() {
  return document.documentElement.classList.contains("dark");
}

describe("theme", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("follows the system colour scheme and its changes", () => {
    const system = stubSystemTheme(true);

    initTheme();
    expect(isDark()).toBe(true);

    system.change(false);
    expect(isDark()).toBe(false);
  });

  it("keeps a chosen theme when the system changes and across reloads", () => {
    const system = stubSystemTheme(false);
    initTheme();

    toggleTheme();
    expect(isDark()).toBe(true);
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("dark");

    system.change(true);
    system.change(false);
    expect(isDark()).toBe(true);

    initTheme();
    expect(getTheme()).toBe("dark");
  });

  it("follows the system again after choosing the look it already has", () => {
    const system = stubSystemTheme(false);
    initTheme();

    toggleTheme();
    toggleTheme();
    expect(isDark()).toBe(false);
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull();

    system.change(true);
    expect(isDark()).toBe(true);
  });

  it("ignores a stored value it doesn't know", () => {
    stubSystemTheme(true);
    window.localStorage.setItem(STORAGE_KEY, "sepia");

    initTheme();
    expect(getTheme()).toBe("dark");
  });

  it("still toggles when storage is blocked", () => {
    stubSystemTheme(false);
    initTheme();
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });

    toggleTheme();
    expect(isDark()).toBe(true);
  });

  it("picks up a change made in another tab", () => {
    stubSystemTheme(false);
    initTheme();

    window.localStorage.setItem(STORAGE_KEY, "dark");
    window.dispatchEvent(new StorageEvent("storage", { key: STORAGE_KEY }));
    expect(isDark()).toBe(true);
  });

  it("tells subscribers until they unsubscribe", () => {
    stubSystemTheme(false);
    initTheme();
    const listener = vi.fn<() => void>();

    const unsubscribe = subscribeToTheme(listener);
    toggleTheme();
    expect(listener).toHaveBeenCalledTimes(1);

    unsubscribe();
    toggleTheme();
    expect(listener).toHaveBeenCalledTimes(1);
  });
});
