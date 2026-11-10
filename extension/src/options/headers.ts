import type { Header } from "../lib/settings.ts";

// HTTP header names: letters, digits and a few symbols, no spaces.
const HEADER_NAME = /^[!#$%&'*+.^_`|~0-9A-Za-z-]+$/;

// One "Name: value" per line; blank lines are skipped.
export function parseHeaders(text: string): Header[] {
  const headers: Header[] = [];
  for (const [index, rawLine] of text.split("\n").entries()) {
    const line = rawLine.trim();
    if (!line) continue;
    const colon = line.indexOf(":");
    const name = line.slice(0, colon).trim();
    if (colon < 1 || !HEADER_NAME.test(name)) {
      throw new Error(`Header line ${index + 1} should look like "Name: value".`);
    }
    headers.push({ name, value: line.slice(colon + 1).trim() });
  }
  return headers;
}

export function formatHeaders(headers: Header[]): string {
  return headers.map(({ name, value }) => `${name}: ${value}`).join("\n");
}
