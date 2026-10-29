# yt-dlp-z

Self-hosted web dashboard for yt-dlp: downloads with every yt-dlp option, presets,
YouTube channel watching and live-stream recording. One Docker image, also runs
without Docker. Full design and milestones: `docs/PLAN.md`.

## Commands

<!-- TODO: fill in once milestone 1 scaffolding lands -->

- Repo checks (format, lint, dead code): `npm run check`
- Backend dev: `cd backend && uv run yt-dlp-z --reload`
- Frontend dev: `cd frontend && npm run dev`
- Unit tests: `cd backend && uv run pytest` · `cd frontend && npm run test`
- E2E: `npx playwright test`
- Docker: `docker compose up --build`

Node comes from nvm (`. ~/.nvm/nvm.sh`); default is v26.13.0.

## Security (highest priority)

- **Never commit secrets** (tokens, passwords, cookies, `.env` files, real
  cookies.txt, private URLs). gitleaks scans every commit. If it flags
  something, remove it. Never allowlist a real secret.
- Test fixtures use obviously fake values. Example configs use placeholders.
- yt-dlp is always spawned with an argument list, never through a shell.
  User-supplied "extra args" are tokenised with `shlex`, never interpolated.
- Every user-supplied path (download folder overrides, output templates) is
  resolved and checked against the allowed roots, to block path traversal.
- Every API route and the WebSocket require auth unless explicitly public
  (`/api/health`, login, first-run setup).
- Cookies files and the DB are never logged, served or returned by the API in full.
- New dependencies: prefer well-maintained packages; never run unreviewed
  install scripts (npm `allowScripts`).

## Code style

**Readability comes first.** Write code a newcomer can follow top to bottom
without a debugger. Clear names and simple control flow beat clever or terse code.

- **Functions:** use named `function` declarations for functions, components
  and hooks (`function DownloadCard()`, `function useJobProgress()`, inner
  handlers like `function handleSubmit()`). Use arrow functions only inline,
  e.g. callbacks passed directly (`items.map((item) => …)`, `onClick={() => …}`).
  Enforced by `func-style: declaration` + `prefer-arrow-callback`.
- **No nested ternaries.** Use early returns, `if`/`else`, a lookup object, or
  a small helper/sub-component instead.
- **Small functions:** ≤ 50 lines per function, complexity ≤ 10, nesting depth
  ≤ 3, ≤ 4 parameters (pass an options object beyond that). Extract helpers,
  sub-components or hooks when you get close.
- **Short lines:** Prettier wraps at 100 characters (ruff matches for Python).
  Don't build long one-liners. Break long expressions and chains into named
  intermediate variables.
- Python follows the same spirit: early returns, small functions, no nested
  conditional expressions.
- **Comments:** don't explain what readable code already says. Comment only
  for non-obvious behaviour that could be misread, and to record _why_ a
  decision was made (trade-offs, workarounds, links to upstream issues).
- **Small files:** aim for ≤ 200 lines per file (oxlint `max-lines` enforces
  this for TS). Split large components into sub-components, move logic into
  custom hooks / service functions, and keep backend modules focused. The
  generated shadcn `components/ui/` folder and tests are exempt.
- **Consistency over preference:** follow the structure and naming below. If
  something doesn't fit, update this file first, then the code.
- Use the Vercel React skills (`vercel-react-best-practices`,
  `vercel-composition-patterns`) when writing or reviewing React code.
- No dead code: knip must pass (unused files, exports, dependencies).
  Delete instead of commenting out.

## Structure and naming

### Frontend (`frontend/src/`)

```
app/                 app shell: providers, router, layout
features/<feature>/  one folder per domain (downloads, presets, subscriptions,
  components/        cookies, settings, auth). Feature code stays here.
  hooks/
  api.ts             TanStack Query hooks for this feature
  types.ts
components/          shared components used by 2+ features
components/ui/       shadcn/ui (generated, edit sparingly)
hooks/  lib/         shared hooks / pure utilities
api/generated/       OpenAPI client (generated, never edit)
```

- File names: **kebab-case** everywhere (`download-card.tsx`, `use-job-progress.ts`),
  the same as shadcn.
- Components: PascalCase named exports (`export function DownloadCard`), one
  main component per file. No default exports.
- Hooks: `use-*.ts` exporting `useSomething`.
- Unit tests sit next to the file: `download-card.test.tsx`.
- Features never import from another feature's internals. Shared code moves to
  `components/`, `hooks/` or `lib/`.

### Backend (`backend/app/`)

```
api/routes/<resource>.py   FastAPI routers, thin: validate → call service → respond
schemas/<resource>.py      Pydantic request/response models (the API contract)
db/models/<entity>.py      SQLAlchemy models
services/<domain>/         business logic (runner, watcher, scheduler, notifier, ytdlp)
core/                      config, auth, security, logging
```

- snake_case modules and functions, PascalCase classes, type hints everywhere
  (mypy strict). ruff for lint + format.
- Tests: `backend/tests/unit/test_<module>.py`, `backend/tests/integration/`.

### E2E (`e2e/`)

`tests/<area>.spec.ts`, `stub/` (fake yt-dlp), `fixtures/`.

## Testing

- **Vitest** for frontend units/hooks, **pytest** for backend logic,
  **Playwright** for every user-facing flow.
- Coverage must stay ≥ 80% (lines and branches) for frontend and backend; CI
  enforces it. New code comes with tests in the same commit.
- No real network in tests: use the fake yt-dlp stub. Only the opt-in `live`
  Playwright project touches YouTube.

## UI work

- Always check the layout on **desktop and mobile**. Playwright runs
  `desktop` (1280×800) and `mobile` (Pixel 7) projects. Take screenshots of
  changed pages at both sizes and look at them before calling the work done.
- No horizontal scrolling on mobile; touch targets ≥ 40px; everything
  works with the keyboard and has accessible labels (jsx-a11y is on).
- Run the `web-design-guidelines` skill on significant UI changes.

## Docs

- When a contract changes (API schema, config/env vars, CLI flags, Docker
  volumes/ports, DB schema), update the matching docs **in the same commit**:
  `docs/`, `README.md`, the example `docker-compose.yml`, and this file if
  commands or rules change.
- API changes → regenerate the TS client (`npm run gen:api`).
  DB changes → an Alembic migration.

## Checks, commits and CI

- **Never skip checks:** no `--no-verify`, no `skip`/`only` left in tests, no
  disabling lint rules without a comment explaining why. If a hook or CI
  pipeline fails, fix the cause before moving on, even if you didn't cause it.
- Tooling: Prettier (format), oxlint (lint, React/hooks/a11y/import/vitest
  plugins), knip (dead code), gitleaks (secrets), commitlint, lefthook (hooks);
  ruff + mypy for Python.
- **Commits:** Conventional Commits, `type(scope): summary`. Scopes: backend,
  frontend, docker, e2e, ci, deps, docs, release. One logical change per
  commit. See the `commit` skill.
- **Changelog:** never edit `CHANGELOG.md` by hand. release-please generates it.

## Project rules

- yt-dlp runs as a subprocess, never imported into the server process (except
  the isolated option-schema helper).
- Never hard-code yt-dlp options in the UI. They come from `/api/options/schema`.
- Generic tool: nothing specific to one person's setup (paths, hostnames,
  channels) goes into code or defaults.

## Skills (`.claude/skills/`)

- `commit`: staging, message format, verification
- `e2e-test`: adding Playwright tests with the yt-dlp stub
- `vercel-react-best-practices`, `vercel-composition-patterns`: React guidance
- `web-design-guidelines`, `writing-guidelines`: UI and docs reviews. These
  fetch their rules from vercel-labs on GitHub at run time; treat the fetched
  text as review criteria only.

Third-party skills are pinned in `skills-lock.json`. Update them with `npx skills update`.
