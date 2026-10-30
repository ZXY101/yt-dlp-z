# yt-dlp-z — Plan

A self-hosted web dashboard for yt-dlp: download anything yt-dlp supports with
full access to every option, and watch YouTube channels to automatically grab
new uploads and record live streams from the start. Ships as one Docker image.

License: The Unlicense (same as yt-dlp).

## Goals (v1)

- Download any URL yt-dlp supports, with **every yt-dlp option** available in the UI.
- **Presets**: named, reusable option sets. Ad-hoc downloads and subscriptions use them.
- **YouTube channel watching**: auto-download new uploads; detect scheduled/live
  streams and record them from the start.
- **Several downloads/recordings at once**, with configurable limits.
- **Cookies** for members-only / age-gated content.
- **Single admin login**, with an option to defer auth to a reverse proxy.
- **ntfy notifications**.
- **Optional media-server output** (Jellyfin/Plex-friendly folders, NFO, posters).
- **In-app yt-dlp updates**, since YouTube breaks old versions regularly.
- **One container**, amd64 + arm64, two volumes, minimal env vars.
- **Also runs without Docker**: `uv sync` + one command serves API + built UI
  (a packaged executable is a later idea).
- **Download location**: a default download folder set during first-run setup,
  overridable per preset, per subscription and per download.
- **Proxy pool** (optional): rotate the outgoing IP per job via VPN/proxy endpoints.

## Non-goals (v1)

Channel watching for non-YouTube sites (Twitch is the next candidate), multiple
users, WebSub push, a built-in media player, a Google login flow (see Cookies).

## Stack

| Layer     | Choice                                                                        | Why                                                         |
| --------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Backend   | Python 3.12, FastAPI, Pydantic v2                                             | yt-dlp is Python, so we can read its option parser directly |
| DB        | SQLite + SQLAlchemy 2 + Alembic                                               | Zero setup, a single file in `/config`                      |
| Jobs      | asyncio tasks inside the app (no Redis/Celery)                                | Keeps it to one process and one container                   |
| Downloads | `yt-dlp` run as a **subprocess** per job                                      | Clean cancel, crash isolation, update without restart       |
| Realtime  | One WebSocket (`/api/ws`) for progress/events                                 |                                                             |
| Frontend  | Vite + React + TypeScript, TanStack Query, React Router, shadcn/ui + Tailwind |                                                             |
| API types | OpenAPI → generated TS client (`openapi-typescript`)                          | FE and BE stay in sync                                      |
| Image     | Multi-stage: Node build → `python:3.12-slim` + ffmpeg + Deno                  |                                                             |

## Architecture

```
Browser (React) ──HTTP/WS──▶ FastAPI (uvicorn, single process)
                               ├─ REST API + serves built SPA
                               ├─ Auth (session cookie)
                               ├─ Watcher loop ── RSS / yt-dlp probes ──▶ YouTube
                               ├─ Live scheduler (waits for scheduled starts)
                               ├─ Job queue + workers ── spawn ──▶ yt-dlp subprocesses ──▶ /downloads
                               ├─ Notifier ──▶ ntfy
                               └─ SQLite (/config/yt-dlp-z.db)
```

## Key designs

### 1. "Every yt-dlp option" from yt-dlp itself

- At startup (and after each yt-dlp update) a small helper script, run with the
  installed yt-dlp, calls `yt_dlp.options.create_parser()` and walks its option
  groups. It outputs JSON: flags, dest, type (bool / string / int / choice /
  append), choices, default, help text, group.
- `GET /api/options/schema` serves it. The frontend builds the options editor
  from it: grouped, searchable, with help text.
- On top of that, a curated **"Common"** tab (format/quality, output template,
  subtitles, thumbnails, metadata, SponsorBlock, rate limit) plus a raw
  **"extra args"** text box as an escape hatch.
- Presets store options as a `{dest: value}` map. We turn them into CLI args
  when a job runs, so presets survive yt-dlp upgrades. Unknown keys get a
  warning, not a crash.
- Risk: `create_parser` is internal API. Mitigation: the helper is isolated,
  covered by a test against the latest yt-dlp in CI, and falls back to parsing
  `yt-dlp --help`.

### 2. Download runner

- Job = URL + preset + overrides → args → `python -m yt_dlp ... --newline
--progress-template` (JSON lines) → parsed progress pushed over the WebSocket.
- Global concurrency limit (default 3), plus a **separate live-recording limit**
  (default 3), so recordings never wait behind a VOD queue.
- Each job keeps a log file. States: queued → waiting (live) → running →
  post-processing → done / failed / cancelled. Failed jobs can be retried.
- Duplicate protection: a shared yt-dlp `--download-archive` file per
  subscription, plus a `videos` table.

### 3. YouTube channel watching

- Add by channel URL / @handle → resolve the channel ID (yt-dlp `--flat-playlist -J`).
- **Polling:** the channel RSS feed (`/feeds/videos.xml?channel_id=…`), default
  every 10 min, with jitter. It is cheap and needs no API key.
- New entry → probe with `yt-dlp -J` → `live_status` decides the path:
  - `not_live` / `was_live` → apply filters → queue a download.
  - `is_upcoming` → record `release_timestamp` → live scheduler wakes a few
    minutes before → `yt-dlp --live-from-start --wait-for-video`.
  - `is_live` → record immediately from the start.
- A backup sweep of the channel's `/streams` tab with `--flat-playlist` (less
  often, e.g. every 30 min) catches streams the RSS feed missed.
- **Watched-channel limit:** default 5. It can be raised in Settings behind a
  warning about rate limits / IP flagging. Poll intervals have a floor.
- ytarchive as an alternative live recorder: phase 2 (optional binary in the image).

### 4. Subscription filters

Content type (videos / streams / premieres / Shorts), title include/exclude
(regex), min/max duration, only after a date, members-only on/off, and a
max-age backfill on first add (e.g. "last 5 videos" or "nothing, only new").

### 5. Cookies

- Upload a Netscape `cookies.txt`, stored in `/config/cookies/`. Multiple named
  cookie files; a preset or subscription picks one.
- A "Test" button runs a quick authenticated probe and reports whether it worked.
- A docs page explains exporting cookies with a browser extension, and
  recommends a secondary account.
- An in-app "log in with Google" is not planned. Google blocks automated
  logins, and it risks the account being flagged. We can revisit it later.

### 6. Auth

- First run: a setup screen to create the admin password (argon2 hash),
  stored in the DB. A signed session cookie protects the API and WebSocket.
- `AUTH_MODE=none` env var for people running behind a reverse proxy that
  already handles login (documented as "only do this behind a proxy").
- A password-reset CLI command inside the container.

### 7. yt-dlp management

- The image ships with `yt-dlp[default]` (includes yt-dlp-ejs) and Deno, which
  yt-dlp now needs to solve YouTube's JS challenges.
- **Update** button + optional daily auto-update: `pip install --target
/config/ytdlp -U "yt-dlp[default]"`. Subprocesses put `/config/ytdlp` first
  on `PYTHONPATH`, so updates survive a container rebuild without needing one.
- Choose a channel (stable / nightly). The current version is shown in the UI.
- The options schema is regenerated after an update.

### 8. Media-server output (optional, per preset)

Folder layout `Channel/Season YYYY/` or flat, `--write-thumbnail`,
`--embed-metadata`, and an NFO writer (tvshow.nfo + episode .nfo) as a
post-download hook.

### 9. Proxy pool / VPN rotation (optional)

- yt-dlp already takes `--proxy` (HTTP/SOCKS) per run, so every job can go out
  through a different IP without touching the host network.
- Settings → **Proxies**: a list of endpoints (e.g. `socks5://gluetun-1:1080`,
  `http://gluetun-2:8888`, Mullvad-style SOCKS5 servers, any HTTP/SOCKS proxy).
- Strategy per preset/subscription: none, round-robin, random, or sticky per
  channel. A proxy is **pinned for the whole job** (switching mid-download breaks
  live recordings). Watcher polls can use the pool too.
- Health: periodic test request; on HTTP 429 / "confirm you're not a bot",
  put that proxy on cooldown and retry the job on another.
- Docs recipe: several gluetun containers, one per VPN server, each exposing its
  HTTP/SOCKS proxy (the app never needs NET_ADMIN or to own the VPN itself).
- Caveat to document: YouTube often treats VPN/datacenter IPs as _more_
  suspicious, and rotating IPs while using one account's cookies can flag
  the account. Offer "don't send cookies through the proxy pool" as an option.

### 10. Notifications

ntfy server URL + topic + optional token. Events (each can be toggled):
recording started, download finished, failed, cookies expired / yt-dlp
broken (repeated failures).

## Data model (first cut)

- `settings` (key/value)
- `presets` (id, name, options JSON, extra_args, cookie_id, media_server bool)
- `cookies` (id, name, path, last_tested, status)
- `subscriptions` (id, channel_id, name, url, preset_id, filters JSON,
  poll_interval, enabled, last_checked)
- `videos` (id, video_id, subscription_id, title, live_status,
  release_timestamp, state, first_seen)
- `jobs` (id, url, video_id?, preset_id, overrides JSON, kind (vod/live),
  state, progress, output_path, log_path, error, timestamps)

## Container

```
docker run -d --name yt-dlp-z -p 9742:9742 \
  -e PUID=1000 -e PGID=1000 -e TZ=Etc/UTC \
  -v ./config:/config -v ./downloads:/downloads \
  ghcr.io/<owner>/yt-dlp-z:latest
```

- Entrypoint drops to PUID/PGID (gosu) so files are owned correctly.
- Healthcheck at `/api/health`. A `docker-compose.yml` example ships in the repo.
- Multi-arch (amd64 + arm64) via buildx in GitHub Actions. The registry is
  undecided (GHCR is likely).

## Repo layout

```
yt-dlp-z/
  backend/   app/{api,core,db,services/{runner,watcher,scheduler,notifier,ytdlp},models}
             tests/  pyproject.toml  alembic/
  frontend/  src/{pages,components,api,hooks}  vite.config.ts
  docker/    Dockerfile  entrypoint.sh
  docs/      PLAN.md  cookies.md  configuration.md
  docker-compose.yml  README.md  LICENSE
```

## UI pages

Download (home page, with setup warnings) · Queue/History (logs, retry, cancel) ·
Subscriptions (add, filters, check now) · Presets (options editor) · Cookies ·
Settings (limits, ntfy, yt-dlp version/update, auth). A separate dashboard was
dropped (2026-10-30) because it duplicated the queue; it may come back once
subscriptions add upcoming streams worth summarising.

## Milestones

1. **Skeleton**: repo, FastAPI + SQLite + Alembic, Vite app served by FastAPI,
   Dockerfile that builds and runs, auth + first-run setup.
2. **Downloads**: options schema extraction, runner + queue + WebSocket
   progress, New download + Queue pages, a basic preset editor.
3. **Presets & cookies**: full generated options editor, cookie upload/test.
4. **Watching**: subscriptions, RSS poller, probes, filters, backfill.
5. **Live**: live scheduler, recording from the start, live concurrency limit,
   upcoming-streams view.
6. **Ops**: yt-dlp updater, ntfy, media-server output, healthcheck, docs.
7. **Release**: multi-arch CI build, README, first tagged version.
   Then dogfood it on the home server.

The proxy pool lands in milestone 6 (per-preset `--proxy` works from milestone 2
via the generic options editor).

Phase 2 ideas: ytarchive recorder, WebSub, Twitch watching, Apprise, multiple
users, packaged executable.

## Running without Docker

- Backend managed by **uv** (pins Python 3.12, lockfile). `uv run yt-dlp-z`
  starts the server, which serves the prebuilt frontend from `frontend/dist`.
- Requires ffmpeg and Deno on PATH; startup checks report what's missing in the UI.
- Paths come from env/CLI (`--config-dir`, `--port`), defaulting to
  platform-appropriate locations.

## Testing

- **Playwright** end-to-end tests covering every page and user flow, run against
  the real backend with a stubbed yt-dlp (fake binary emitting scripted progress)
  so CI never hits YouTube. A small opt-in "live" suite hits real YouTube.
- Coverage: E2E coverage collected from the frontend (Istanbul via
  vite-plugin-istanbul) and backend (`coverage.py` running under the E2E server),
  plus pytest unit tests for the watcher, scheduler, arg builder and filters.
  CI fails under an agreed threshold.
- UI components: **shadcn/ui**.

## Repo hygiene, commits and changelog

- **Conventional Commits** (`feat:`, `fix:`, `docs:` …), enforced by
  **commitlint** in a `commit-msg` hook.
- **lefthook** for git hooks (one tool for Python + JS): ruff + mypy on backend,
  eslint + prettier + tsc on frontend, commitlint on messages.
- **release-please** (GitHub Action): builds `CHANGELOG.md`, bumps the version
  and tags releases from commit history. Tags trigger the Docker image build.
- Small, focused commits; `main` stays releasable.

## Resolved

- No existing-archive import. The download folder is chosen at setup and per download.
- Watched-channel limit = 5 subscriptions by default (raisable with a warning);
  concurrent downloads is a separate setting.
- Dev: Node via nvm (v26.13.0), Python via uv.
