# Progress

Where the project stands. Update this at the end of every working session, so
the next session (or contributor) can pick up without other context.
Design and milestones: [PLAN.md](PLAN.md).

## Current status

**Milestone 1 (skeleton): done.** Next up: **Milestone 2 (downloads).**

| Milestone                 | Status      |
| ------------------------- | ----------- |
| 0. Repo foundation        | Done        |
| 1. Skeleton               | Done        |
| 2. Downloads              | Not started |
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

## Next steps (Milestone 2)

1. Add yt-dlp (`yt-dlp[default]`), ffmpeg and Deno to the image; check what
   yt-dlp currently needs for YouTube (JS runtime, PO tokens) before starting.
2. Option schema: isolated helper that reads yt-dlp's parser →
   `GET /api/options/schema`, with a fallback and a test against the latest yt-dlp.
3. Jobs: `jobs` table + migration, subprocess runner with JSON progress
   parsing, concurrency limit, cancel/retry, per-job log file.
4. Realtime: authenticated WebSocket for job progress.
5. Download path checks: per-download folder overrides validated against the
   allowed roots (path traversal).
6. UI: New download page (URL, folder, common options, raw extra args),
   Queue/History page with live progress.
7. E2E: fake yt-dlp stub (`e2e/stub/`) emitting scripted progress, wired via
   an env var for the yt-dlp binary.

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
