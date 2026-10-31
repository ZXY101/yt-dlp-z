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

### Proxy pool

Settings → **Proxies** holds HTTP or SOCKS proxies (`http://`, `https://`,
`socks4://`, `socks4a://`, `socks5://`, `socks5h://`, with `user:password@` if
needed). Passwords are stored in the database but never shown again. **Test**
opens a page through the proxy with yt-dlp's own networking and shows the IP
address sites see (from Cloudflare's `/cdn-cgi/trace`), then checks that
YouTube answers.

A preset (or a single download) picks how its downloads use the pool: **Off**,
**Next proxy in turn**, **Random proxy**, or **Same proxy per channel**
(subscriptions keep one proxy; one-off downloads take turns). The proxy is
picked when a download starts and kept until it ends. If yt-dlp fails with
YouTube's "confirm you're not a bot", HTTP 429 or a proxy connection error,
that proxy is skipped for 30 minutes and the download tries the next one (up
to 3). Recordings aren't retried, but the proxy still cools down. A download
that should use the pool never falls back to a direct connection: with no
proxy free it fails, and can be retried.

Downloads with cookies connect directly unless **Send downloads with cookies
through proxies** is on: one account seen from many IP addresses can get
flagged, and the cookies identify it anyway. Channel checks (feeds, link
checks) don't use the pool yet.

YouTube often asks VPN and data-centre addresses to sign in, so a VPN proxy may
work better for other sites than for YouTube. One way to get several exit IPs:
one [gluetun](https://github.com/qdm12/gluetun) container per VPN server, each
with its HTTP proxy on (`HTTPPROXY=on`), on the same Docker network as yt-dlp-z:

```yaml
services:
  vpn-1:
    image: qmcgaw/gluetun
    cap_add: [NET_ADMIN]
    devices: [/dev/net/tun:/dev/net/tun]
    environment:
      VPN_SERVICE_PROVIDER: your-provider
      SERVER_COUNTRIES: Netherlands
      HTTPPROXY: "on"
      # plus your provider's credentials
```

Then add `http://vpn-1:8888` as a proxy. yt-dlp-z itself never needs
`NET_ADMIN` or a VPN of its own.

### Updating yt-dlp

YouTube changes often break older yt-dlp versions. Settings → yt-dlp updates it
without a new app release: **Update now** pip-installs the newest
`yt-dlp[default]` (Stable, or Nightly pre-releases) into `<config>/ytdlp`. That
folder comes first on `PYTHONPATH` for every yt-dlp run, so the update survives
container rebuilds and app updates. Downloads already running keep the version
they started with. **Use bundled version** deletes the folder. The install goes
to a staging folder first, so a failed update never breaks the yt-dlp in use.
Updating needs internet access to PyPI. The app checks for a newer version a
minute after it starts and then once a day (Settings shows "X is available");
turn on **Update automatically** to install it then. It's off by default.

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
