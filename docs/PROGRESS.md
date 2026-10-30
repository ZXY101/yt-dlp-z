# Progress

Where the project stands. Update this at the end of every working session, so
the next session (or contributor) can pick up without other context.
Design and milestones: [PLAN.md](PLAN.md).

## Current status

**Milestone 4 (watching): done.** Next up: **Milestone 5 (live).**

| Milestone                 | Status      |
| ------------------------- | ----------- |
| 0. Repo foundation        | Done        |
| 1. Skeleton               | Done        |
| 2. Downloads              | Done        |
| 3. Presets & cookies      | Done        |
| 4. Watching               | Done        |
| 5. Live                   | Not started |
| 6. Ops (incl. proxy pool) | Not started |
| 7. Release                | Not started |

What exists: FastAPI backend with first-run setup, login/logout, rate limiting,
`AUTH_MODE=none` and a `reset-password` command; download jobs (queue, live
progress over WebSocket, cancel/retry/log); presets; cookies files (upload,
test, per download/preset); runtime settings (download folder, download
limit, channel limit); channel subscriptions (RSS poller, yt-dlp probe, filters,
backfill, per-video history). React frontend: Download (home, with preset/cookies pickers and a
searchable editor for every yt-dlp option), Queue, Subscriptions, Presets,
Cookies, Settings.
Vitest, pytest and Playwright suites; Docker image; CI for all of it.

## Playlist downloads (steps 1–2 done 2026-10-30)

Reported 2026-10-30: pasting a playlist link downloaded every video without
warning. Now (`features/downloads/playlist-link.ts`, URL parsing, YouTube only):

1. Done: `watch?v=…&list=…` / `youtu.be/…?list=…` links show "Just this video"
   (default, `--no-playlist`) / "The whole playlist" (`--yes-playlist`). The
   choice overrides either flag set in the options.
2. Done: `/playlist?list=…` and channel links (`/@x`, `/channel/`, `/c/`,
   `/user/`, any tab) show a notice that every video will be downloaded.
3. Later: the queue card says "playlist" and which item it is on
   ("video 3 of 24"), from yt-dlp's playlist_index / n_entries. Needs the stub
   to emit several items for a playlist URL.

## Next steps (Milestone 5)

See PLAN.md "YouTube channel watching" (the `is_upcoming` / `is_live` paths).
Subscriptions already record such videos as `upcoming` (with `release_at`) or
`live` in the `videos` table; nothing records them yet.

1. Live scheduler: wake a few minutes before `release_at`, then run
   `yt-dlp --live-from-start --wait-for-video` as a job (jobs need a "live"
   kind or flag, and the UI a "recording" state).
2. `live` videos: start recording immediately from the start.
3. Separate live concurrency limit (recordings shouldn't block downloads).
4. Backup sweep of the channel's `/streams` tab with `--flat-playlist`
   (every ~30 min) for streams the RSS feed misses.
5. Stub: upcoming/live behaviour for recordings; E2E for every flow.
6. Small follow-ups from M4: the video list shows probe titles only for probed
   videos (skipped-before-subscribing ones keep the feed title, which is fine);
   consider a "download anyway" action on skipped videos.
7. Proposed to the user, not yet approved: a "download the newest N now" action
   on the edit page (backfill after adding). It would re-run the newest N
   "Uploaded before you subscribed" videos through probe → filters → queue.
   The RSS feed caps it at 15; more needs yt-dlp `--flat-playlist` on /videos.

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
- Watching: feed entries are probed with `yt-dlp -J` one at a time; the poller
  checks due subscriptions one after another (30 s tick), to keep the request
  rate low. Content types are video / Short / stream; premieres count as
  streams because yt-dlp reports both through `live_status`.
- The first check is the one with `last_checked_at` unset; only successful
  checks set it. Failed checks are throttled by an in-memory attempt time.
- Failed probes are retried on every check while the video is in the feed.
  Members-only videos that yt-dlp can't open without cookies count as
  "Members-only" (skipped) unless members-only is included.
- Subscription downloads copy the preset's options at queue time, like the
  download form. Subscription cookies override the preset's.
- `max_subscriptions` in `PUT /api/settings` is required, so an old client
  can't silently reset a raised limit.
- Tests: pytest points `YTDLPZ_YOUTUBE_FEED_URL` at `file://` feeds; E2E uses
  the test server's own `/api/test/feeds/{channel_id}`.

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
- **2026-10-30 · Small fixes.** Pointer cursor on buttons (Tailwind v4 dropped
  it). "Save to" suggests existing folders (`GET /api/folders`, only inside the
  allowed roots, no files, hidden folders and escaping symlinks skipped) via a
  native datalist, loaded on focus and per typed `/`.
- **2026-10-30 · Milestone 4 done.** Subscriptions backend (219 backend tests,
  96%), Subscriptions page + channel limit in Settings (149 unit tests, 98%),
  63 E2E tests (8 new, desktop + mobile). Fixed a leak found by the new tests:
  the option-schema reader wasn't killed when the app stopped. Screenshots
  checked at desktop and mobile. Pushed.
- **2026-10-30 · UI fixes.** Empty states are clickable (open the add page, or
  focus the cookies upload form). Dark-mode `<select>` options were unreadable
  on Chrome/Windows (white popup, light text): options now use the popover
  colours. "Save to" replaced its `<datalist>` (misplaced, unthemeable popup)
  with an ARIA combobox (`hooks/use-suggestion-list.ts`); picking a folder adds
  a trailing slash. Pushed (b7a31c5). A Docker "page loads forever" report
  turned out to be the browser's network path, not the app (no requests reached
  the container); fixed on the user's side.

- **2026-10-30 · Playlist links.** Video-in-playlist links ask "Just this
  video" / "The whole playlist"; playlist and channel links show a notice.
  Parser unit tests, 3 page tests, 3 E2E tests (desktop + mobile), screenshots
  checked in light and dark.

**Next session:** ask about backfill-on-edit (M5 step 7), then milestone 5
step 1. Playlist step 3 (queue progress) can wait. `cd ~/dev/yt-dlp-z && git pull && npm run check`.
