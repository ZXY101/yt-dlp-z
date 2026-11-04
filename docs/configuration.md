# Configuration

yt-dlp-z is configured with environment variables (prefix `YTDLPZ_`) or
command-line flags. Flags win over environment variables.

## Environment variables

| Variable                           | Default (native)            | Default (Docker)       | Purpose                                                                                                             |
| ---------------------------------- | --------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `YTDLPZ_HOST`                      | `127.0.0.1`                 | `0.0.0.0`              | Address to listen on                                                                                                |
| `YTDLPZ_PORT`                      | `9742`                      | `9742`                 | Port to listen on                                                                                                   |
| `YTDLPZ_CONFIG_DIR`                | your user data folder¹      | `/config`              | Database, secret key, job logs and uploaded cookies                                                                 |
| `YTDLPZ_DEFAULT_DOWNLOAD_DIR`      | `~/Downloads/yt-dlp-z`      | `/downloads`           | Suggested download folder in first-run setup                                                                        |
| `YTDLPZ_AUTH_MODE`                 | `password`                  | `password`             | `password`, or `none` to turn off login. **Only use `none` behind a proxy that handles login.**                     |
| `YTDLPZ_ADMIN_PASSWORD`            | unset                       | unset                  | Sets the admin password up front (see below)                                                                        |
| `YTDLPZ_SESSION_DAYS`              | `30`                        | `30`                   | How long a sign-in lasts                                                                                            |
| `YTDLPZ_MAX_CONCURRENT_DOWNLOADS`  | `3`                         | `3`                    | How many downloads run at once; the rest wait. Changing it on the Settings page overrides this                      |
| `YTDLPZ_MAX_CONCURRENT_RECORDINGS` | `2`                         | `2`                    | How many live recordings run at once, counted apart from downloads. Changing it on the Settings page overrides this |
| `YTDLPZ_EXTRA_DOWNLOAD_ROOTS`      | `[]`                        | `[]`                   | Extra absolute folders downloads may use, as a JSON list, e.g. `["/media/music"]`                                   |
| `YTDLPZ_ALLOW_UNSAFE_OPTIONS`      | `false`                     | `false`                | Allows the unsafe yt-dlp options listed below. Only for trusted setups.                                             |
| `YTDLPZ_CHAT_FONT`                 | unset                       | unset                  | Font file embedded in live chat overlays ([details](live-chat.md#fonts)).                                           |
| `YTDLPZ_YTDLP_COMMAND`             | the bundled yt-dlp          | the bundled yt-dlp     | Command that runs yt-dlp, as a JSON list (mainly for tests)                                                         |
| `YTDLPZ_YTDLP_PIP_COMMAND`         | the app's own pip           | the app's own pip      | pip used for yt-dlp updates, as a JSON list (only for tests)                                                        |
| `YTDLPZ_PROXY_CHECK_COMMAND`       | the app's own check         | the app's own check    | Runs a proxy's Test, reading the address on stdin, as a JSON list (only for tests)                                  |
| `YTDLPZ_YOUTUBE_FEED_URL`          | YouTube's channel feed      | YouTube's channel feed | Feed polled for new uploads; `{channel_id}` is filled in (only for tests)                                           |
| `YTDLPZ_FRONTEND_DIST`             | `frontend/dist` in the repo | `/app/frontend`        | Folder with the built web UI                                                                                        |

¹ e.g. `~/.local/share/yt-dlp-z` on Linux.

### Setting the admin password up front

By default the first person to open a fresh install chooses the admin
password. On a server reachable by others, set `YTDLPZ_ADMIN_PASSWORD`
instead: setup then asks for that password rather than creating one, so nobody
else can claim the install.

The variable is applied at every start. Changing it and restarting replaces
the password and signs out every session. While it is set, `reset-password`
only lasts until the next restart.

### Download folders

Each download goes to the default folder chosen during setup, unless another
folder is given for that download:

- empty: the default folder
- a relative path, e.g. `music/albums`: a sub-folder of the default folder
- an absolute path: only inside the default folder or one of
  `YTDLPZ_EXTRA_DOWNLOAD_ROOTS`

Paths are resolved (including `..` and symlinks) before this check, so a
download can't escape these folders. File name templates (`--output`) must be
relative for the same reason.

### Feature settings

Most settings live in the app, on the Settings page or per preset. Each feature
has its own guide:

- [Cookies](cookies.md): members-only and age-restricted videos
- [Subscriptions](subscriptions.md): check interval, channel limit, filters, retention
- [Live recording](live-recording.md): recording settings and VODs
- [Media servers](media-server.md): Jellyfin / Plex / Kodi output
- [Proxies](proxies.md): the proxy pool
- [Notifications](notifications.md): ntfy
- [yt-dlp and PO tokens](ytdlp.md): updates, PO tokens and the
  [blocked yt-dlp options](ytdlp.md#blocked-options) (`YTDLPZ_ALLOW_UNSAFE_OPTIONS`)

### Test mode

`YTDLPZ_TEST_MODE` exists for the automated test suite only. Never set it on a
real install: it exposes an endpoint that wipes all data.

### Docker only

| Variable      | Default | Purpose                                                     |
| ------------- | ------- | ----------------------------------------------------------- |
| `PUID`/`PGID` | `1000`  | User and group that own files in `/config` and `/downloads` |
| `TZ`          | UTC     | Time zone for logs and schedules                            |

## Command line

```
yt-dlp-z [--host HOST] [--port PORT] [--config-dir DIR] [--reload]
yt-dlp-z reset-password     # set a new admin password and sign out every session
yt-dlp-z openapi            # print the API schema as JSON
```

In Docker: `docker exec -it yt-dlp-z yt-dlp-z reset-password`.

## Volumes (Docker)

| Path         | Contents                                                                                                                                                                                                                 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/config`    | `yt-dlp-z.db` (settings, presets, subscriptions, password hash), `secret.key`, `logs/`, `cookies/`, and `ytdlp/` / `plugins/` from in-app updates. Back this up, and keep it private: `cookies/` holds sign-in sessions. |
| `/downloads` | Default download location chosen in first-run setup                                                                                                                                                                      |

## Security notes

- The admin password is stored as an argon2 hash. Sign-ins use a signed,
  HTTP-only cookie. Changing the password signs out every session.
- After 5 failed sign-ins within a minute, that address is blocked for a minute.
- Behind a reverse proxy, forward `X-Forwarded-For` and `X-Forwarded-Proto`
  so rate limiting and secure cookies use the real client details.
