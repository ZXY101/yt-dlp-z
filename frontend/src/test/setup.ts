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

class StubResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

// jsdom has neither; Radix components (e.g. Checkbox) need ResizeObserver.
window.matchMedia = stubMatchMedia;
globalThis.ResizeObserver = StubResizeObserver;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
