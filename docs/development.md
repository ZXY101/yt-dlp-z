# Development setup

## Prerequisites

| Tool                | Why                                 | Install                                                                                      |
| ------------------- | ----------------------------------- | -------------------------------------------------------------------------------------------- |
| Node (see `.nvmrc`) | frontend, E2E, repo tooling         | [nvm](https://github.com/nvm-sh/nvm): `nvm install && nvm use`                               |
| uv                  | Python 3.12 + backend dependencies  | [docs.astral.sh/uv](https://docs.astral.sh/uv/)                                              |
| gitleaks            | secret scan in the pre-commit hook  | `brew install gitleaks` or a [release binary](https://github.com/gitleaks/gitleaks/releases) |
| ffmpeg, Deno        | needed by yt-dlp (from milestone 2) | your package manager / [deno.com](https://deno.com)                                          |
| Docker (optional)   | building and running the image      |                                                                                              |

## First-time setup

```sh
nvm use
npm install                                  # all JS workspaces; installs git hooks
(cd backend && uv sync)                      # Python env in backend/.venv
(cd e2e && npx playwright install chromium)  # browser for E2E tests
```

## Running locally

Two terminals:

```sh
cd backend && uv run yt-dlp-z --reload    # API on http://127.0.0.1:8080
npm run dev -w frontend                   # UI on http://localhost:5173, proxies /api
```

To try the production setup without Docker, run `npm run build -w frontend`,
then `cd backend && uv run yt-dlp-z`, and open http://127.0.0.1:8080.

Local data lives in your user data folder (see [configuration](configuration.md)).
Pass `--config-dir ./tmp-config` to keep a throwaway instance separate.

## Repository layout

```
backend/   FastAPI app (src/yt_dlp_z), pytest tests, Alembic migrations
frontend/  React app (npm workspace)
e2e/       Playwright tests (npm workspace)
docker/    Dockerfile and entrypoint
docs/      plan, progress, configuration, this guide
```

## Checks and tests

```sh
npm run check                                   # Prettier, oxlint, knip
cd backend && uv run ruff check . && uv run mypy && uv run pytest
npm run typecheck -w frontend && npm run test:coverage -w frontend
npm test -w e2e                                 # builds the UI, starts its own server
```

Git hooks (lefthook) run format, lint, type and secret checks on commit and the
unit tests on push. CI runs everything, including E2E and a Docker build. Never
bypass hooks with `--no-verify`; fix the failure instead.

Both backend and frontend fail below 80% test coverage.

## Changing the API or database

- API: after changing routes or schemas, run `npm run gen:api -w frontend` and
  commit the regenerated `frontend/src/api/generated/schema.d.ts`. CI fails if
  it is stale.
- Database: add the model under `db/models/`, import it in
  `migrations/env.py`, then `cd backend && uv run alembic revision --autogenerate -m "…"`.
  Migrations run automatically at startup.

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/), for example
`feat(frontend): add download queue page`. release-please builds the changelog
and releases from them.
