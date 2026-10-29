import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";

function stubMatchMedia(query: string): MediaQueryList {
  return {
    matches: false,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  };
}

// jsdom has no matchMedia.
window.matchMedia = stubMatchMedia;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
