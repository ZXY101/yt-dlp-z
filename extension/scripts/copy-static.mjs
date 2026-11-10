// tsc only emits the scripts; the manifest, pages, styles and icons are copied as they are.
import { cpSync } from "node:fs";

cpSync(new URL("../static", import.meta.url), new URL("../dist", import.meta.url), {
  recursive: true,
});
