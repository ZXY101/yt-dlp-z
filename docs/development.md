# Development setup

## Prerequisites

| Tool                | Why                         | Install                                                                                      |
| ------------------- | --------------------------- | -------------------------------------------------------------------------------------------- |
| Node (see `.nvmrc`) | frontend, repo tooling      | [nvm](https://github.com/nvm-sh/nvm): `nvm install && nvm use`                               |
| uv                  | Python 3.12 + backend deps  | [docs.astral.sh/uv](https://docs.astral.sh/uv/)                                              |
| gitleaks            | secret scan in pre-commit   | `brew install gitleaks` or a [release binary](https://github.com/gitleaks/gitleaks/releases) |
| ffmpeg, Deno        | needed by yt-dlp at runtime | your package manager / [deno.com](https://deno.com)                                          |
| Docker (optional)   | building/running the image  |                                                                                              |

## First-time setup

```sh
nvm use
npm install        # repo tooling; also installs the git hooks (lefthook)
```

Backend and frontend setup steps are added in Milestone 1.

## Checks

```sh
npm run check      # Prettier, oxlint, knip
```

Commits run gitleaks, Prettier, oxlint and commitlint through lefthook. CI runs
the same checks on every push and pull request. Never bypass them with `--no-verify`.

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/), for example
`feat(frontend): add download queue page`. release-please builds the changelog
and releases from them.
