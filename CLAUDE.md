# yt-dlp-z

Self-hosted web dashboard for yt-dlp: downloads with every yt-dlp option, presets,
YouTube channel watching and live-stream recording. One Docker image, also runs
without Docker. Full design and milestones: `docs/PLAN.md`.

## Layout

- `backend/` — Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, SQLite. Managed with **uv**.
- `frontend/` — Vite + React + TypeScript, TanStack Query, shadcn/ui + Tailwind.
- `e2e/` — Playwright tests (run against the real backend with a stubbed yt-dlp).
- `docker/` — Dockerfile + entrypoint.
- `docs/` — plan, user docs.

## Commands

<!-- TODO: fill in once milestone 1 scaffolding lands -->
- Backend dev: `cd backend && uv run yt-dlp-z --reload`
- Frontend dev: `cd frontend && npm run dev`
- Unit tests: `cd backend && uv run pytest`
- E2E: `npx playwright test`
- Docker: `docker compose up --build`

Node comes from nvm (`. ~/.nvm/nvm.sh`); default is v26.13.0.

## House rules

<!-- Draft — edit freely. -->
- **Commits:** Conventional Commits (`feat(backend): …`, `fix(frontend): …`).
  Scopes: backend, frontend, docker, e2e, ci, deps, docs, release. commitlint
  enforces this. Keep commits small and focused, one logical change each.
- **Changelog:** never edit `CHANGELOG.md` by hand. release-please generates it
  from commit messages, so write messages for users to read.
- **yt-dlp runs as a subprocess**, never imported into the server process
  (except the isolated option-schema helper).
- **Never hard-code yt-dlp options in the UI.** They come from
  `/api/options/schema`. Curated "Common" fields map onto the same option dests.
- **No real network in tests.** Use the fake yt-dlp stub. Only the opt-in
  `live` suite touches YouTube.
- **Every user-facing feature ships with a Playwright test.** Backend logic
  (watcher, scheduler, filters, arg builder) gets pytest unit tests.
- **Generic tool:** nothing specific to one person's setup (paths, hostnames,
  channels) goes into code or defaults.
- API changes → regenerate the TS client (`npm run gen:api`) in the same commit.
- DB schema changes → an Alembic migration in the same commit.

## Skills

Project skills live in `.claude/skills/`:
- `commit` — how to stage, write and verify a commit
- `e2e-test` — how to add a Playwright test with the yt-dlp stub
- `house-rules` — placeholder for more conventions as they emerge
