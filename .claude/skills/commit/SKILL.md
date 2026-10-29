---
name: commit
description: Make a clean Conventional Commit in yt-dlp-z. Use whenever committing changes in this repo.
---

# Commit

1. `git status` / `git diff` — split unrelated changes into separate commits.
2. Make sure checks pass for what you touched (lefthook runs them on commit,
   but run them first to avoid a failed commit loop).
3. Message format: `type(scope): summary` in the imperative, ≤ 72 chars.
   - types: feat, fix, perf, refactor, docs, test, build, ci, chore
   - scopes: backend, frontend, docker, e2e, ci, deps, docs, release
   - breaking change: `feat(backend)!: …` + a `BREAKING CHANGE:` footer
   - `feat`/`fix` lines land in the changelog, so write them for users.
4. Body (optional): why, not what.
5. Never `--no-verify`. If a hook fails, fix the cause.

<!-- TODO: add examples from real commits once there's history -->
