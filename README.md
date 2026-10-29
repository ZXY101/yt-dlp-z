# yt-dlp-z

A self-hosted web dashboard for [yt-dlp](https://github.com/yt-dlp/yt-dlp).

- Download from any site yt-dlp supports, with every yt-dlp option available
- Reusable presets
- Watch YouTube channels: new uploads download automatically, live streams are
  recorded from the start
- Cookies for members-only content, ntfy notifications, optional proxy rotation
- One Docker container, or run it directly

> Status: early development. Setup and sign-in work; downloading arrives in the
> next milestone. See [docs/PROGRESS.md](docs/PROGRESS.md).

## Quick start (Docker)

```sh
git clone https://github.com/ZXY101/yt-dlp-z.git && cd yt-dlp-z
docker compose up -d --build
```

Open http://localhost:9742 and finish the first-run setup: choose the admin
password and the default download folder. The first visitor gets to choose,
so if others can reach the server, set `YTDLPZ_ADMIN_PASSWORD` in
`docker-compose.yml` first (see [configuration](docs/configuration.md)).

Files land in `./downloads`, and settings live in `./config`. Set `PUID`/`PGID`
in `docker-compose.yml` to the user that should own them.

## Without Docker

Needs Node (see `.nvmrc`) and [uv](https://docs.astral.sh/uv/).

```sh
npm install && npm run build -w frontend
cd backend && uv run yt-dlp-z
```

Then open http://127.0.0.1:9742.

## Documentation

- [Configuration](docs/configuration.md): environment variables, CLI, volumes
- [Development](docs/development.md): local setup, tests, conventions
- [Plan](docs/PLAN.md) and [progress](docs/PROGRESS.md)

## License

[The Unlicense](LICENSE), the same as yt-dlp.
