# Progress

Where the project stands. Update this at the end of every working session, so
the next session (or contributor) can pick up without other context.
Design and milestones: [PLAN.md](PLAN.md).

## Current status

**Milestone 2 (downloads): done.** Next up: **Milestone 3 (presets & cookies).**

| Milestone                 | Status      |
| ------------------------- | ----------- |
| 0. Repo foundation        | Done        |
| 1. Skeleton               | Done        |
| 2. Downloads              | Done        |
| 3. Presets & cookies      | Not started |
| 4. Watching               | Not started |
| 5. Live                   | Not started |
| 6. Ops (incl. proxy pool) | Not started |
| 7. Release                | Not started |

What exists: FastAPI backend with first-run setup (admin password + default
download folder), login/logout, rate limiting, `AUTH_MODE=none`, and a
`reset-password` command. React frontend with setup, login, a responsive app
shell and an empty dashboard. Vitest, pytest and Playwright suites; Docker
image; CI for all of it.

## Next steps (Milestone 3)

1. Presets: `presets` table + migration, CRUD API, options stored by long flag
   (same format as jobs), default preset, pick a preset on the download page.
2. Full options editor generated from `GET /api/options/schema`: grouped,
   searchable, help text, blocked options shown disabled with the reason.
3. Cookies: upload Netscape `cookies.txt` (stored in `/config/cookies`, never
   returned in full), name, test button, choose per preset/download; the app
   passes `--cookies` itself (users can't).
4. Settings page: download folder, max concurrent downloads.
5. E2E for every new flow; regression tests for any bug found.

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

## Open items

- Docker image is 784 MB, mostly Debian's ffmpeg. A static ffmpeg build could
  shrink it a lot.
- release-please fails until "Allow GitHub Actions to create and approve pull
  requests" is enabled in the repo settings (waiting on the maintainer).
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
