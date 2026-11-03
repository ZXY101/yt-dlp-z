# Installation

yt-dlp-z runs as one Docker container, or directly with Python and Node. Both
serve the web app and the API on one port (9742 by default).

## Requirements

- **Docker**: any 64-bit Linux, macOS or Windows host with Docker and Docker
  Compose. The image includes yt-dlp, FFmpeg and Deno.
- **Without Docker**: [Node](https://nodejs.org) (version in `.nvmrc`, only to
  build the web app), [uv](https://docs.astral.sh/uv/) (installs Python 3.12 and
  the backend), [FFmpeg](https://ffmpeg.org) and [Deno](https://deno.com) on
  the `PATH`. yt-dlp needs FFmpeg to merge and convert files, and Deno to solve
  YouTube's JavaScript challenges.
- Disk space for your downloads. Live recordings of long streams can be tens of
  gigabytes.

## Docker Compose

```sh
git clone https://github.com/ZXY101/yt-dlp-z.git
cd yt-dlp-z
docker compose up -d --build
```

The repository's `docker-compose.yml`:

```yaml
services:
  yt-dlp-z:
    image: ghcr.io/zxy101/yt-dlp-z:latest
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: yt-dlp-z
    ports:
      - "9742:9742"
    environment:
      PUID: 1000
      PGID: 1000
      TZ: Etc/UTC
      # Recommended if others can reach the server: setup will ask for this password.
      # YTDLPZ_ADMIN_PASSWORD: change-me
      # Uncomment only if a reverse proxy in front of the app handles login.
      # YTDLPZ_AUTH_MODE: none
    volumes:
      - ./config:/config
      - ./downloads:/downloads
    restart: unless-stopped
    stop_grace_period: 10m
```

What to change:

- **`PUID` / `PGID`**: the user and group that should own `/config` and the
  downloaded files. Run `id` on the host to find yours.
- **`TZ`**: your time zone (e.g. `Europe/Amsterdam`), for logs and schedules.
- **`./downloads`**: point it at your media folder, e.g.
  `/mnt/media/YouTube:/downloads`. Mount more folders and list them in
  `YTDLPZ_EXTRA_DOWNLOAD_ROOTS` to download into them too (see
  [Configuration](configuration.md#download-folders)).
- **`YTDLPZ_ADMIN_PASSWORD`**: set it if anyone else can reach the port before
  you finish setup.
- **`stop_grace_period`**: keep it. When the container stops, running
  recordings get up to 10 minutes to finish their files (merging, embedding
  the thumbnail). Docker's default of 10 seconds cuts them off.

Pre-built images aren't published yet, so `--build` builds the image from the
source (a few minutes the first time). The image is a multi-stage build:
Node builds the web app, uv installs the backend into a slim Python image with
FFmpeg and Deno. It has a health check on `/api/health`.

### Plain `docker run`

```sh
docker build -f docker/Dockerfile -t yt-dlp-z .
docker run -d --name yt-dlp-z \
  -p 9742:9742 \
  -e PUID=1000 -e PGID=1000 -e TZ=Etc/UTC \
  -v "$PWD/config:/config" -v "$PWD/downloads:/downloads" \
  --stop-timeout 600 \
  --restart unless-stopped \
  yt-dlp-z
```

## Without Docker

```sh
git clone https://github.com/ZXY101/yt-dlp-z.git && cd yt-dlp-z
npm install && npm run build -w frontend   # builds the web app into frontend/dist
cd backend && uv run yt-dlp-z              # http://127.0.0.1:9742
```

By default it listens on `127.0.0.1` only. Use `--host 0.0.0.0` (or
`YTDLPZ_HOST`) to reach it from other devices. Settings, the database and logs
go to your user data folder (`~/.local/share/yt-dlp-z` on Linux) unless you
pass `--config-dir`. The suggested download folder is `~/Downloads/yt-dlp-z`.

### As a systemd service

```ini
# /etc/systemd/system/yt-dlp-z.service
[Unit]
Description=yt-dlp-z
After=network-online.target
Wants=network-online.target

[Service]
User=youruser
WorkingDirectory=/opt/yt-dlp-z/backend
ExecStart=/usr/local/bin/uv run --frozen yt-dlp-z --host 0.0.0.0
Restart=on-failure
# Give running recordings time to finish their files.
TimeoutStopSec=600

[Install]
WantedBy=multi-user.target
```

Then `sudo systemctl enable --now yt-dlp-z`. Adjust the paths to where you
cloned the repository and where `uv` is installed (`which uv`).

## First-run setup

Open the app in a browser. The setup page asks for:

1. **The admin password** (or, when `YTDLPZ_ADMIN_PASSWORD` is set, that
   password to confirm it's you).
2. **The default download folder**. In Docker, keep `/downloads`.

Then you're signed in. Sign-ins last 30 days by default
(`YTDLPZ_SESSION_DAYS`).

Good next steps:

- Create a few [presets](presets.md), e.g. "Best quality", "Audio only (MP3)"
  and a "Live streams" preset.
- Add a [cookies file](cookies.md) if you download members-only videos.
- Set up [notifications](notifications.md) and, for heavy YouTube use, the
  [PO-token provider](ytdlp.md#po-tokens).

### Forgot the password

```sh
docker exec -it yt-dlp-z yt-dlp-z reset-password   # Docker
cd backend && uv run yt-dlp-z reset-password       # without Docker
```

It asks for a new password and signs out every session.

## Behind a reverse proxy

yt-dlp-z works behind any reverse proxy. Two things matter:

- **WebSockets** on `/api/ws` must be proxied (live progress and updates).
- **`X-Forwarded-For` and `X-Forwarded-Proto`** must be forwarded, so sign-in
  rate limiting sees the real client address and cookies are marked secure
  over HTTPS.

Serve it at the root of its own (sub)domain; a sub-path such as
`example.com/yt-dlp-z/` isn't supported.

**Caddy**

```caddy
ytdlp.example.com {
	reverse_proxy 127.0.0.1:9742
}
```

**nginx**

```nginx
server {
    listen 443 ssl;
    server_name ytdlp.example.com;

    location / {
        proxy_pass http://127.0.0.1:9742;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 10m;   # cookies.txt uploads
    }
}
```

In Nginx Proxy Manager, turn on **Websockets Support** for the proxy host.

### Letting the proxy handle login

If your proxy already does authentication (Authelia, Authentik, oauth2-proxy,
Tailscale, basic auth…), set `YTDLPZ_AUTH_MODE=none` to turn off yt-dlp-z's own
login. **Only do this when the app's port can't be reached any other way**:
with `none`, anyone who reaches the port has full access.

## Updating

**Docker:**

```sh
cd yt-dlp-z
git pull
docker compose up -d --build
```

**Without Docker:**

```sh
git pull
npm install && npm run build -w frontend
# restart the service (or `cd backend && uv run yt-dlp-z`)
```

Database changes are applied automatically at start. Read the
[changelog](../CHANGELOG.md) before updating across several versions.

yt-dlp itself can be updated from the app without updating yt-dlp-z; see
[yt-dlp and PO tokens](ytdlp.md).

## Backups

Back up the config folder (`/config` in Docker). It holds:

| File / folder | Contents                                                             |
| ------------- | -------------------------------------------------------------------- |
| `yt-dlp-z.db` | Settings, presets, subscriptions, download history, password hash    |
| `secret.key`  | Signs sign-in cookies. Losing it only signs everyone out             |
| `cookies/`    | Uploaded cookies files. **These are sign-in sessions: keep private** |
| `logs/`       | One log per download                                                 |
| `ytdlp/`      | yt-dlp installed by an in-app update (can be re-created)             |
| `plugins/`    | The PO-token plugin (can be re-created)                              |

For a consistent copy of the database, stop the container first, or use
`sqlite3 yt-dlp-z.db ".backup backup.db"` while it runs.

## Uninstalling

Stop and remove the container (`docker compose down`), then delete the config
folder. Your downloads stay where they are.
