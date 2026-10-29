# Progress

Where the project stands. Update this at the end of every working session, so
the next session (or contributor) can pick up without other context.
Design and milestones: [PLAN.md](PLAN.md).

## Current status

**Milestone 0 (repo foundation): done.** Next up: **Milestone 1 (skeleton).**

| Milestone                 | Status      |
| ------------------------- | ----------- |
| 0. Repo foundation        | Done        |
| 1. Skeleton               | Not started |
| 2. Downloads              | Not started |
| 3. Presets & cookies      | Not started |
| 4. Watching               | Not started |
| 5. Live                   | Not started |
| 6. Ops (incl. proxy pool) | Not started |
| 7. Release                | Not started |

## Next steps (Milestone 1)

1. `backend/`: uv project (Python 3.12), FastAPI app factory, settings, SQLite +
   SQLAlchemy + Alembic, `/api/health`, ruff + mypy + pytest with coverage.
2. Auth: first-run setup (admin password + default download folder), login,
   session cookie, `AUTH_MODE=none`.
3. `frontend/`: Vite + React + TS, Tailwind + shadcn/ui, TanStack Query,
   React Router, Vitest with coverage; served by FastAPI in production.
4. `e2e/`: Playwright with `desktop` + `mobile` projects, the server fixture
   and the fake yt-dlp stub skeleton.
5. `docker/`: multi-stage Dockerfile, entrypoint (PUID/PGID), compose example.
6. Extend lefthook and CI with backend/frontend checks and coverage gates.
7. Fill in the Commands section of CLAUDE.md.

## Decisions not obvious from the code

- Inner handlers in components use `function handleX()`, not `const` arrows
  (confirmed by the maintainer; enforced by `func-style`).
- Downloads: any yt-dlp site. Channel watching: YouTube only (Twitch later).
- The watched-channel limit of 5 counts subscriptions, not concurrent downloads.
- No import of existing archives. The download folder is chosen at first-run
  setup and can be overridden per preset, subscription and download.
- In-app Google login was rejected (Google blocks automated logins). Cookies
  are uploaded instead.

## Log

- **2026-10-29/30:** Plan written. Repo set up with Conventional Commits
  (commitlint), lefthook, release-please, Prettier, oxlint (readability +
  React rules), knip, gitleaks, CI `checks` workflow, Vercel agent skills,
  CLAUDE.md house rules. Pushed to github.com/ZXY101/yt-dlp-z (private).
