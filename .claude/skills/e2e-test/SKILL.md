---
name: e2e-test
description: Add or update Playwright end-to-end tests for yt-dlp-z features. Use when adding a user-facing feature or fixing a UI bug.
---

# E2E test

<!-- Draft — finalise once the e2e/ harness exists (milestone 1–2). -->

- Tests live in `e2e/tests/<area>.spec.ts`, one file per page/flow.
- The test server starts the real backend with a temp config dir and
  `YTDLPZ_YTDLP_BIN` pointing at the fake yt-dlp stub (`e2e/stub/`), which
  emits scripted progress/output. Never hit YouTube outside the `live` project.
- Prefer role/label locators (`getByRole`, `getByLabel`) over CSS selectors.
  Add `data-testid` only when there's no accessible handle.
- Every spec runs in both the `desktop` and `mobile` projects. Assert
  layout-sensitive things (menus, tables → cards) at both sizes.
- Cover the happy path, the main error state, and persistence (reload the page).
- Check coverage didn't drop: `npm run test:e2e:coverage`.
