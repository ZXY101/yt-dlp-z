# Configuration

yt-dlp-z is configured with environment variables (prefix `YTDLPZ_`) or
command-line flags. Flags win over environment variables.

## Environment variables

| Variable                      | Default (native)            | Default (Docker) | Purpose                                                                                         |
| ----------------------------- | --------------------------- | ---------------- | ----------------------------------------------------------------------------------------------- |
| `YTDLPZ_HOST`                 | `127.0.0.1`                 | `0.0.0.0`        | Address to listen on                                                                            |
| `YTDLPZ_PORT`                 | `9742`                      | `9742`           | Port to listen on                                                                               |
| `YTDLPZ_CONFIG_DIR`           | your user data folder¹      | `/config`        | Database and secret key                                                                         |
| `YTDLPZ_DEFAULT_DOWNLOAD_DIR` | `~/Downloads/yt-dlp-z`      | `/downloads`     | Suggested download folder in first-run setup                                                    |
| `YTDLPZ_AUTH_MODE`            | `password`                  | `password`       | `password`, or `none` to turn off login. **Only use `none` behind a proxy that handles login.** |
| `YTDLPZ_SESSION_DAYS`         | `30`                        | `30`             | How long a sign-in lasts                                                                        |
| `YTDLPZ_FRONTEND_DIST`        | `frontend/dist` in the repo | `/app/frontend`  | Folder with the built web UI                                                                    |

¹ e.g. `~/.local/share/yt-dlp-z` on Linux.

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

| Path         | Contents                                                                |
| ------------ | ----------------------------------------------------------------------- |
| `/config`    | `yt-dlp-z.db` (settings, password hash) and `secret.key`. Back this up. |
| `/downloads` | Default download location chosen in first-run setup                     |

## Security notes

- The admin password is stored as an argon2 hash. Sign-ins use a signed,
  HTTP-only cookie. Changing the password signs out every session.
- After 5 failed sign-ins within a minute, that address is blocked for a minute.
- Behind a reverse proxy, forward `X-Forwarded-For` and `X-Forwarded-Proto`
  so rate limiting and secure cookies use the real client details.
