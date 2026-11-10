# yt-dlp-z browser extension

Sends the current page or a right-clicked link to your own yt-dlp-z server, which downloads
or records it. Nothing is downloaded in the browser. Chrome and Firefox (desktop and
Android) from one Manifest V3 codebase, plain TypeScript compiled by `tsc`: no bundler, so
the published files are the readable compiler output.

Needs a yt-dlp-z server 0.1.6 or newer and an API token made under Settings → API tokens
with “Send links only”.

## Development

From the repo root:

| What                    | Command                            |
| ----------------------- | ---------------------------------- |
| Build into `dist/`      | `npm run build -w extension`       |
| Types                   | `npm run typecheck -w extension`   |
| Unit tests              | `npm test -w extension`            |
| Re-render toolbar icons | `node extension/scripts/icons.mjs` |

Load the build:

- Chrome: `chrome://extensions` → Developer mode → Load unpacked → `extension/dist`.
- Firefox: `about:debugging#/runtime/this-firefox` → Load Temporary Add-on →
  `extension/dist/manifest.json`.

## Layout

```
src/background/  service worker (Chrome) / event page (Firefox): every request, menus, badge
src/popup/       toolbar popup
src/options/     connection settings
src/lib/         shared: server client, storage, link-type guess
static/          manifest, pages, styles, icons (copied into dist/ as they are)
```

Every request goes through the background script, so closing the popup mid-request loses
nothing. The extension asks for host permission only for the server address the user
enters, and has no content scripts, so it can't read page contents.
