# Progress

Where the project stands. Update this at the end of every working session, so
the next session (or contributor) can pick up without other context.
Design and milestones: [PLAN.md](PLAN.md).

## Current status

**Milestone 6 (ops): in progress.** Steps 1–2 (yt-dlp updates) done; next is
step 3 (ntfy notifications). Milestone 5 is done (a real scheduled stream starting
on time is still unchecked, see below).

| Milestone                 | Status      |
| ------------------------- | ----------- |
| 0. Repo foundation        | Done        |
| 1. Skeleton               | Done        |
| 2. Downloads              | Done        |
| 3. Presets & cookies      | Done        |
| 4. Watching               | Done        |
| 5. Live                   | Done        |
| 6. Ops (incl. proxy pool) | In progress |
| 7. Release                | Not started |

What exists: FastAPI backend with first-run setup, login/logout, rate limiting,
`AUTH_MODE=none` and a `reset-password` command; download jobs (queue, live
progress over WebSocket, cancel/retry/log); presets; cookies files (upload,
test, per download/preset); runtime settings (download folder, download
limit, channel limit); channel subscriptions (RSS poller, yt-dlp probe, filters,
backfill, per-video history); live recording (scheduled/queued recordings in their
own queue, live scheduler, streams-tab sweep). React frontend: Download (home, with preset/cookies pickers and a
searchable editor for every yt-dlp option), Queue, Subscriptions, Presets,
Cookies, Settings.
Vitest, pytest and Playwright suites; Docker image; CI for all of it.

## Milestone 6 steps

1. **yt-dlp updater: done 2026-10-31.** `services/ytdlp/updater.py`,
   `/api/ytdlp`, Settings → yt-dlp (version, Stable/Nightly, Update now, Use
   bundled version). pip installs `yt-dlp[default]` (`--pre` for nightly) into
   `<config>/ytdlp` via a staging folder; that folder is first on PYTHONPATH for
   every yt-dlp subprocess. An install equal to the bundled version deletes the
   folder instead (back from nightly to stable). `pip` is a dependency (uv venvs
   have none). Verified for real (local server and in the Docker image):
   stable 16 s, nightly gave 2026.10.29.232701dev and `/api/system` (a
   subprocess) reported it. E2E uses `e2e/stub/fake_pip.py`.
2. **Update checks and auto-update: done 2026-10-31.**
   `services/ytdlp/update_check.py`: `pip install --dry-run --report -`
   resolves the version an update would install (0.6 s, writes nothing, same
   index/proxy as the real update; no extra dependency). Runs 1 min after
   start, then daily; the result is kept in memory. Settings → yt-dlp shows
   "X is available", has Check for updates, and "Update automatically" (off
   by default: an update changes what every later download runs). API:
   `PUT /api/ytdlp/preferences` (channel + auto_update; replaced
   `/channel`), `POST /api/ytdlp/check`.
3. ntfy notifications (PLAN.md §10).
4. Media-server output per preset (PLAN.md §8).
5. Proxy pool (PLAN.md §9).
6. PO-token provider (bgutil) recipe.
7. Docs: configuration.md, ops; healthcheck review.

## Link check on the download form (done 2026-10-31)

Asked by the maintainer: no more blind submits. Typing a link checks it with
yt-dlp after a 0.6 s pause (`POST /api/media/probe`: `-J --flat-playlist`,
first 50 entries, with the chosen cookies) and shows a card (thumbnail, title,
uploader, site, duration / count / start time). Download stays disabled until
the check passes; failures show yt-dlp's message (members-only explains it
needs a member's cookies). The answer picks the form: playlists and channels
show what will be downloaded (with the real count), YouTube videos opened from
a playlist keep the "just this video / whole playlist" choice (the check looks
at whichever is picked), live streams offer "from the start / from now" and a
**Record** button, upcoming streams **Schedule recording**. Recordings use
`POST /api/jobs` with `recording`. A real channel link answers with its tabs
(Videos, Live, Shorts), so a playlist of playlists is reported as a channel.
`--ignore-no-formats-error` is only added on a retry when yt-dlp says the
stream "will begin" / "premieres in": on every run it turned unavailable videos
and ended streams into empty results that passed (found on real YouTube
2026-10-31). Verified on real YouTube: video, live (`@LofiGirl/live`), ended
stream, made-up id, playlist (150), channel. Known gap: the check doesn't pass
the form's options, so a link that only works through `--proxy` fails the check.

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

## Milestone 5 notes

Done 2026-10-30: streams found by a subscription (feed or streams-tab sweep)
become `kind: live` jobs; upcoming ones wait as `scheduled` and the live
scheduler (`services/live/scheduler.py`) queues them 5 min before
`release_at`; recordings have their own queue and limit; interrupted
recordings restart by themselves after a restart. Queue shows a "Scheduled"
list and a "Recording" badge; Settings has "Recordings at the same time".

Still open:

1. **Real-YouTube check, partly done 2026-10-30.** Sweep + probe worked on real
   channels; a 60 s real recording (Lofi Girl) worked. It found two bugs, both
   fixed: upcoming streams failed the probe (needs `--ignore-no-formats-error`)
   and recordings showed no progress (parallel `N: ` prefixed lines). Split
   recordings checked on real YouTube too (valid parts, stops at the maximum);
   that found from-now parts showing no progress (ffmpeg's `\r` progress lines),
   fixed. Still to see: a real scheduled stream starting on time, and a
   finished file after a stream ends. Consider an opt-in `live` Playwright test.
2. **24/7 and long streams: done 2026-10-30.** Settings → Recordings (all
   combinable, each can be turned off): new file every N hours (default 6, so
   a 24/7 stream records forever in parts), stop after N hours (default off),
   record from the start unless live longer than N hours (default 6, else
   from now). Each part is its own yt-dlp run stopped with SIGINT, so parts
   are merged files; there is a gap of a few seconds between parts. Cancel,
   shutdown and restart keep the file (restart continues as the next part).
   Skipping 24/7 streams is done with title filters. Also a choice for those
   long streams: "Record their first N hours" (from the start, stopped after
   N hours of the stream). The maximum length counts hours of the stream:
   from the start, yt-dlp downloads faster than real time, so it's worked
   out from fragment numbers (`services/live/stream_clock.py`). Verified on
   real YouTube 2026-10-30: a 60 s limit on Lofi Girl (live 72 days) finished
   in ~5 s with a 65 s file. YouTube keeps only the last 120 h, so for older
   streams "first hours" means the earliest 120 h-old part available.
3. A stream rescheduled _earlier_ after we scheduled it is only caught if a
   later check re-probes it (it doesn't today: videos with a job are done).
   Later yt-dlp `--wait-for-video` covers streams that start late.
4. Small follow-ups: "download anyway" on skipped videos; manual recording
   from the Download page (a "record live stream" choice) for non-subscribed
   streams; ytarchive as an alternative recorder (phase 2).
5. Not approved: "download the newest N now" on the edit page (backfill after
   adding). The user said to leave it for now (2026-10-30).

## Decisions not obvious from the code

- Inner handlers in components use `function handleX()`, not `const` arrows
  (confirmed by the maintainer; enforced by `func-style`).
- Recording settings are global and copied onto each live job when it is
  created; per-subscription overrides could come later.
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

- Recordings: `JobQueues` (`services/jobs/queues.py`) holds two `JobManager`s
  (downloads, recordings) and routes by `job.kind`. Scheduled recordings wait in
  the DB, not in a yt-dlp process, so a premiere a week away holds no slot and
  survives restarts. yt-dlp gets `--live-from-start --wait-for-video 30-300`.
- The streams-tab sweep runs during a normal check when the subscription wants
  streams and the last sweep is 30+ min old; entries only it found are recorded
  if live/upcoming, otherwise skipped ("Found on the streams tab after it
  ended"), so enabling streams later never back-downloads stream history.
- Interrupted downloads fail on restart (Retry by hand); interrupted
  recordings are queued again automatically.
- Subscription jobs start with the feed/probe title, so scheduled recordings
  show a name before yt-dlp runs.

## Open items

- The `layout.spec.ts` "dark mode also darkens native controls" test failed
  once on mobile in a full run (passed 15/15 on repeat). Watch for flakiness.

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

- **2026-10-30 · Deployed + Milestone 5.** Deployed on the maintainer's server.
  Fixed a UI race found by a flaky E2E run: the subscription video list stopped
  polling when a check ended and could miss its last videos. Live recording:
  job kinds, scheduled status, live scheduler, separate recording queue and
  limit (`YTDLPZ_MAX_CONCURRENT_RECORDINGS`), streams-tab sweep, auto-restart of
  interrupted recordings. 225 backend tests (96%), 176 unit tests (98%), 73 E2E.

- **2026-10-30 · Real-YouTube check.** Two fixes from it (upcoming-stream probe,
  recording progress); stub now mimics both real behaviours.

- **2026-10-30 · Split and limited recordings.** Settings → Recordings (parts,
  maximum length, from-start limit); graceful SIGINT stops; ffmpeg progress
  for from-now parts. Verified on real YouTube. 240 backend tests, 75 E2E.
  Deployed ff62e83 on the maintainer's server.

- **2026-10-30 · Settings and options UI.** "Record their first N hours" for
  long streams; Settings section renamed "Live streams"; page width moved into
  the app layout (the queue was full width); all yt-dlp options now open in a
  dialog with group tabs (picker on phones) and search across groups. 247
  backend tests, 179 unit, 76 E2E.

- **2026-10-31 · Link check and updater backend.** Checkbox labels line up
  with the box (`leading-5`); the header name links home. Download form checks
  links before downloading and records live/upcoming streams (see "Link
  check"). yt-dlp updater backend (M6 step 1). Fixed a race the updater tests
  found: `GET /api/ytdlp` read the version before the status.

- **2026-10-31 · Deployed 1c92ffc; updater UI.** Settings → yt-dlp section,
  checked against real PyPI (stable and nightly).

- **2026-10-31 · Update checks.** Daily check, "available" notice, optional
  auto-update (M6 step 2).

**Next session:** M6 step 3 (ntfy), see "Milestone 6 steps". Still unverified: a real scheduled stream starting on time.
`cd ~/dev/yt-dlp-z && git pull && npm run check`.
