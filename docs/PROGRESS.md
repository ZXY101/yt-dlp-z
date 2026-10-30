# Progress

Where the project stands. Update this at the end of every working session, so
the next session (or contributor) can pick up without other context.
Design and milestones: [PLAN.md](PLAN.md).

## Current status

**Milestone 3 (presets & cookies): done.** Next up: **Milestone 4 (watching).**

| Milestone                 | Status      |
| ------------------------- | ----------- |
| 0. Repo foundation        | Done        |
| 1. Skeleton               | Done        |
| 2. Downloads              | Done        |
| 3. Presets & cookies      | Done        |
| 4. Watching               | Not started |
| 5. Live                   | Not started |
| 6. Ops (incl. proxy pool) | Not started |
| 7. Release                | Not started |

What exists: FastAPI backend with first-run setup, login/logout, rate limiting,
`AUTH_MODE=none` and a `reset-password` command; download jobs (queue, live
progress over WebSocket, cancel/retry/log); presets; cookies files (upload,
test, per download/preset); runtime settings (download folder, download
limit). React frontend: Download (home, with preset/cookies pickers and a
searchable editor for every yt-dlp option), Queue, Presets, Cookies, Settings.
Vitest, pytest and Playwright suites; Docker image; CI for all of it.

## Next steps (Milestone 4)

See PLAN.md "YouTube channel watching" and "Subscription filters".

1. `subscriptions` table: channel id/name/url, preset_id, filters JSON, poll
   interval, enabled, last_checked. Add by URL or @handle, resolving the channel
   id with `yt-dlp --flat-playlist -J` (the stub needs a fake for this).
2. `videos` table (seen entries, live_status, release_timestamp, state), so a
   video is only queued once. Jobs get an optional video/subscription link.
3. Poller: channel RSS feed every 10 min with jitter and a floor; new entry →
   probe with `yt-dlp -J` → filters → queue a download with the preset. Live and
   upcoming entries are only recorded as such here (recording is milestone 5).
4. Filters: content type, title include/exclude regex, duration, after date,
   members-only; backfill on first add ("last N" or "only new").
5. Watched-channel limit (default 5, raisable in Settings with a warning).
6. Subscriptions page (add, filters, check now, enable/disable), E2E for every
   flow. No real network in tests: fake RSS served by the test server or stub.

## Decisions not obvious from the code

- Inner handlers in components use `function handleX()`, not `const` arrows
  (confirmed by the maintainer; enforced by `func-style`).
- Downloads: any yt-dlp site. Channel watching: YouTube only (Twitch later).
- The watched-channel limit of 5 counts subscriptions, not concurrent downloads.
- No import of existing archives. The download folder is chosen at first-run
  setup and can be overridden per preset, subscription and download.
- In-app Google login was rejected (Google blocks automated logins). Cookies
  are uploaded instead.
- Backend package is `backend/src/yt_dlp_z` (uv's src layout), not `app/`.
- TypeScript 7 is used for the app. `openapi-typescript` still needs
  TypeScript 5, so `gen:api` runs it through `npx` with a pinned TS 5 and the
  generated types are committed.
- `shadcn` is a dev dependency: only its CSS file is imported, at build time.
- The first visitor to a fresh install sets the admin password, unless
  `YTDLPZ_ADMIN_PASSWORD` is set; then setup must enter that password (it is
  verified and rate-limited), so setup can't be used to bypass it.
- Default port is 9742 (8080 clashes with qBittorrent and others).
- No dashboard page: it only repeated the queue. Download is the home page.
- The download form applies a preset by copying its values into the form; jobs
  store the resolved options, not a preset reference, so editing a preset never
  changes past or queued downloads.
- The curated choices (quality, subtitles, metadata, SponsorBlock) are views
  over the same options map as the full editor, so both always agree.
- Cookies: each yt-dlp run gets a private temporary copy (yt-dlp writes cookies
  back on exit). Jobs keep `cookie_id` without a foreign key; a deleted file
  fails the retry with a clear message, and presets using it are unlinked.
- The download limit set in Settings is stored in the DB and overrides
  `YTDLPZ_MAX_CONCURRENT_DOWNLOADS`. Lowering it lets running downloads finish.
- Rules for all coding agents live in `AGENTS.md`; `CLAUDE.md` imports it.

## Open items

- Docker image is 784 MB, mostly Debian's ffmpeg. A static ffmpeg build could
  shrink it a lot.
- release-please works (Actions may open PRs since 2026-10-30) and releases
  start at 0.1.0. CI doesn't run on its PRs by itself: GITHUB_TOKEN-created PRs
  don't trigger workflows (shown as "action required"). Fine for now; a PAT or
  GitHub App token would fix it if needed.
- PO tokens: YouTube is enforcing them for some clients. The usual fix is the
  bgutil-ytdlp-pot-provider plugin (a helper container) — milestone 6.

- `npm audit`: 3 low-severity advisories in `deepmerge`, pulled in by the
  shadcn CLI (dev only, nothing ships to the browser). No patched version
  exists; npm's suggested fix downgrades shadcn to 1.0. Revisit when shadcn
  updates.
- E2E coverage is not collected yet (unit coverage is gated at 80% on both
  sides). Consider Istanbul instrumentation of the E2E build later.

## Log

- **2026-10-29/30:** Plan written. Repo set up with Conventional Commits
  (commitlint), lefthook, release-please, Prettier, oxlint (readability +
  React rules), knip, gitleaks, CI `checks` workflow, Vercel agent skills,
  CLAUDE.md house rules. Pushed to github.com/ZXY101/yt-dlp-z (private).
- **2026-10-30:** Milestone 1. Backend (35 tests, 99% coverage), frontend
  (34 tests, 99%), Playwright (16 tests, desktop + mobile), Docker image
  (201 MB, runs as PUID/PGID, healthcheck), hooks and CI jobs for all of it.
  Layout checked with screenshots at desktop and mobile sizes.
- **2026-10-30 · M2 in progress (session ended at usage cap).**
  Pushed: `feat!:` port 8080 → 9742; `YTDLPZ_ADMIN_PASSWORD` (setup must enter it;
  env-password E2E project on a 2nd server, port 8766); CLAUDE.md regression rule.
  Committed, **not pushed**: `758e5da feat(backend): download jobs…` (129 tests, 95%).
  **Uncommitted, unverified:** Dockerfile (+ffmpeg, Deno 2.9.8 from
  `denoland/deno:bin-2.9.8`, image not rebuilt), vite WS proxy, regenerated
  `schema.d.ts`, shadcn checkbox/progress/badge/dialog/textarea, the whole
  frontend for downloads/queue/system warnings, the split test fake
  (`src/test/fake-*.ts`), `.oxlintrc.json` (react-perf plugin removed) and the
  CLAUDE.md note about it. Last run: 2 download-page tests failed on
  `ResizeObserver is not defined`; a stub was just added to `src/test/setup.ts`
  but tests were not re-run.
  Still to do for M2: E2E specs for download/queue/cancel/retry/log using the
  stub (`YTDLPZ_YTDLP_COMMAND` in `e2e/scripts/start-server.sh`), desktop+mobile
  screenshots, docker build check, docs (configuration.md: new env vars
  `YTDLPZ_MAX_CONCURRENT_DOWNLOADS`, `YTDLPZ_EXTRA_DOWNLOAD_ROOTS`,
  `YTDLPZ_ALLOW_UNSAFE_OPTIONS`, `YTDLPZ_YTDLP_COMMAND`; blocked-options list).
  release-please CI fails until "Allow GitHub Actions to create and approve pull
  requests" is enabled in repo settings (asked the user, no answer yet).
  PO-token provider (bgutil) noted for milestone 6.
  **Next session:** `cd ~/dev/yt-dlp-z && npx tsc -b frontend && npm run test:coverage -w frontend`,
  fix failures, `npm run check`, then commit frontend + Dockerfile separately.
- **2026-10-30 · Milestone 2 done.** Frontend tests passed after a
  ResizeObserver stub; download/queue/system pages, E2E download flows (27 E2E
  tests), Docker image with ffmpeg + Deno 2.9.8 (verified in a container).
  Bugs found by the new tests and fixed with regression tests: yt-dlp left
  running on shutdown; stale cancel responses overwriting "cancelled" (jobs now
  carry a `revision`); new jobs inheriting a deleted job's log.
- **2026-10-30 · Navigation and AGENTS.md.** Dropped the dashboard (it duplicated
  the queue): Download is now the home page (`/`, shows setup warnings), Queue is
  the second tab, and the "New download" button is gone. Rules moved from
  `CLAUDE.md` to `AGENTS.md` for all agents; `CLAUDE.md` imports it and keeps
  only Claude-specific notes (skills). release-please still needs "Allow GitHub
  Actions to create and approve pull requests" in the repo settings.
- **2026-10-30 · Milestone 3 done.** Dashboard dropped (Download is home),
  AGENTS.md, dark-mode native controls fix. Presets, cookies and settings APIs
  (153 backend tests, 96%), frontend pages and the generated options editor
  (127 unit tests, 98%), 49 E2E tests incl. presets/cookies/settings. The job
  manager now uses a dispatcher with an adjustable limit instead of a fixed
  worker pool. The oxlint hook no longer fails on commits that only stage
  lint-ignored files. Screenshots checked at desktop, mobile and dark mode.
