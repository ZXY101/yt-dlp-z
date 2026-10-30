# Configuration

yt-dlp-z is configured with environment variables (prefix `YTDLPZ_`) or
command-line flags. Flags win over environment variables.

## Environment variables

| Variable                          | Default (native)            | Default (Docker)       | Purpose                                                                                         |
| --------------------------------- | --------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------- |
| `YTDLPZ_HOST`                     | `127.0.0.1`                 | `0.0.0.0`              | Address to listen on                                                                            |
| `YTDLPZ_PORT`                     | `9742`                      | `9742`                 | Port to listen on                                                                               |
| `YTDLPZ_CONFIG_DIR`               | your user data folder¹      | `/config`              | Database, secret key, job logs and uploaded cookies                                             |
| `YTDLPZ_DEFAULT_DOWNLOAD_DIR`     | `~/Downloads/yt-dlp-z`      | `/downloads`           | Suggested download folder in first-run setup                                                    |
| `YTDLPZ_AUTH_MODE`                | `password`                  | `password`             | `password`, or `none` to turn off login. **Only use `none` behind a proxy that handles login.** |
| `YTDLPZ_ADMIN_PASSWORD`           | unset                       | unset                  | Sets the admin password up front (see below)                                                    |
| `YTDLPZ_SESSION_DAYS`             | `30`                        | `30`                   | How long a sign-in lasts                                                                        |
| `YTDLPZ_MAX_CONCURRENT_DOWNLOADS` | `3`                         | `3`                    | How many downloads run at once; the rest wait. Changing it on the Settings page overrides this  |
| `YTDLPZ_EXTRA_DOWNLOAD_ROOTS`     | `[]`                        | `[]`                   | Extra absolute folders downloads may use, as a JSON list, e.g. `["/media/music"]`               |
| `YTDLPZ_ALLOW_UNSAFE_OPTIONS`     | `false`                     | `false`                | Allows the unsafe yt-dlp options listed below. Only for trusted setups.                         |
| `YTDLPZ_YTDLP_COMMAND`            | the bundled yt-dlp          | the bundled yt-dlp     | Command that runs yt-dlp, as a JSON list (mainly for tests)                                     |
| `YTDLPZ_YOUTUBE_FEED_URL`         | YouTube's channel feed      | YouTube's channel feed | Feed polled for new uploads; `{channel_id}` is filled in (only for tests)                       |
| `YTDLPZ_FRONTEND_DIST`            | `frontend/dist` in the repo | `/app/frontend`        | Folder with the built web UI                                                                    |

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

### Cookies

Upload a Netscape-format `cookies.txt` on the Cookies page to download
members-only, private or age-restricted videos. yt-dlp-z stores it in
`<config>/cookies/` readable only by its own user, never returns it through the
API, and passes `--cookies` itself (users can't). Each download gets its own
temporary copy, because yt-dlp writes cookies back when it exits. For YouTube,
export from a private window you then close, so the browser doesn't rotate the
session and invalidate the file.

### Watching channels

The Subscriptions page watches YouTube channels (a channel URL or `@handle`).
Each channel's RSS feed is read every 10 minutes by default (5 at the
least), plus a little random delay so channels don't all poll at once. A new
upload is opened with yt-dlp to see what it is (video, Short, live stream or
premiere), checked against the subscription's filters, and queued with its
preset. On the first check only the newest "backfill" uploads are downloaded;
older ones are marked as seen. Each video is handled once; if yt-dlp can't
open it, it is retried on the next check while it is still in the feed.

Upcoming and live streams are listed but not recorded yet. Members-only
videos need a member's cookies, set on the subscription or its preset.

The Settings page limits how many channels can be watched (5 by default).
Many channels polled from one IP can get it rate-limited or flagged by YouTube.

### Blocked yt-dlp options

Every yt-dlp option is available, except these.

Always blocked, because yt-dlp-z manages them itself: `--paths`, `--cookies`,
`--cookies-from-browser`, `--download-archive`, `--update`, `--update-to`,
`--batch-file`.

Blocked unless `YTDLPZ_ALLOW_UNSAFE_OPTIONS=true`, because they can run programs
or read and write files outside the download folder: `--exec`, `--netrc-cmd`,
`--plugin-dirs`, `--ffmpeg-location`, `--downloader`, `--js-runtimes`,
`--postprocessor-args`, `--downloader-args`, `--load-info-json`,
`--netrc-location`, `--config-locations`, `--print-to-file`, `--cache-dir`,
`--enable-file-urls`, `--alias`.

yt-dlp-z also ignores yt-dlp config files on the server (`--ignore-config`), so
every download uses exactly the options chosen in the app.

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

| Path         | Contents                                                                                                                                                                     |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/config`    | `yt-dlp-z.db` (settings, presets, subscriptions, password hash), `secret.key`, `logs/` and `cookies/`. Back this up, and keep it private: `cookies/` holds sign-in sessions. |
| `/downloads` | Default download location chosen in first-run setup                                                                                                                          |

## Security notes

- The admin password is stored as an argon2 hash. Sign-ins use a signed,
  HTTP-only cookie. Changing the password signs out every session.
- After 5 failed sign-ins within a minute, that address is blocked for a minute.
- Behind a reverse proxy, forward `X-Forwarded-For` and `X-Forwarded-Proto`
  so rate limiting and secure cookies use the real client details.
