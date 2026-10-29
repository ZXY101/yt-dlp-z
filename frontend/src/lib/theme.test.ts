import { applySystemTheme } from "@/lib/theme";

describe("applySystemTheme", () => {
  it("follows the system colour scheme and its changes", () => {
    const captured: { onChange?: () => void } = {};
    const media = {
      matches: true,
      addEventListener(_event: string, callback: () => void) {
        captured.onChange = callback;
      },
    };
    vi.stubGlobal("matchMedia", () => media);

    applySystemTheme();
    expect(document.documentElement).toHaveClass("dark");

    media.matches = false;
    captured.onChange?.();
    expect(document.documentElement).not.toHaveClass("dark");
  });
});
