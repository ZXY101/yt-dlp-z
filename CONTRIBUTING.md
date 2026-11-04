# Contributing to yt-dlp-z

Thanks for helping! Bug reports, ideas, docs fixes and code are all welcome.

## Reporting bugs

[Open an issue](https://github.com/ZXY101/yt-dlp-z/issues/new/choose) with:

- the yt-dlp-z and yt-dlp versions (Settings page)
- how you run it (Docker or not, behind a reverse proxy or not)
- what you did, what you expected, what happened
- the job's **Log** from the Queue page, if a download failed

**Remove cookies, tokens, passwords and private links** before posting.
Download failures that also happen with plain `yt-dlp` on the command line
belong to [yt-dlp's issue tracker](https://github.com/yt-dlp/yt-dlp/issues).

Security problems: please follow [SECURITY.md](SECURITY.md) instead of opening
a public issue.

## Suggesting features

Open a feature request and describe the problem you want solved, not only the
solution. Search the existing issues first; it may already be planned or
decided against.

## Pull requests

1. Read [AGENTS.md](AGENTS.md) (code style, structure, security rules; it's for
   humans too) and the [development guide](docs/development.md).
2. For anything bigger than a small fix, open an issue first so we can agree on
   the approach.
3. Keep each pull request to one logical change, with tests:
   - backend logic → pytest, frontend logic → Vitest
   - every user-facing flow → a Playwright test
   - every bug fix → a regression test that fails without the fix
4. Update the docs in the same pull request when behaviour, settings, the API or
   the database change.
5. Run the checks before pushing:

   ```sh
   npm run check
   cd backend && uv run ruff check . && uv run mypy && uv run pytest
   npm run typecheck -w frontend && npm run test:coverage -w frontend
   npm test -w e2e
   ```

6. Use [Conventional Commits](https://www.conventionalcommits.org/)
   (`feat(frontend): …`, `fix(backend): …`). The changelog is generated from
   them, so never edit `CHANGELOG.md` by hand.

## License

yt-dlp-z is released under [The Unlicense](LICENSE). By contributing you agree
to release your contribution into the public domain under the same terms.
