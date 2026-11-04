# Debug yt-dlp-z

## A download or recording failed

1. Call `get_download` with `log_lines` set to 50. Read `error` and the end of the log.
2. Match the cause in the table below.
3. Call `get_system_status` if the cause might be a missing tool or an old yt-dlp.
4. Explain the cause in a sentence, make the fix or tell the user how, then call
   `retry_download` once. If it fails the same way, stop and report instead of retrying.

Ask before a fix that affects other downloads, such as switching to nightly yt-dlp. Updating
yt-dlp on the current channel is low risk.

| Error or sign                                    | Likely cause                                 | Fix                                                                                                                                                    |
| ------------------------------------------------ | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| "Sign in to confirm you're not a bot"            | YouTube doesn't trust the IP address         | Check `po_tokens` with `get_settings` and suggest PO tokens. Then suggest cookies. Check `proxy_mode`, since VPN exits are often worse than a home IP. |
| HTTP 403, or "Requested format is not available" | Old yt-dlp or a missing PO token             | `update_ytdlp`, then retry. Next, nightly yt-dlp (ask first) and PO tokens.                                                                            |
| Members-only, private or age-restricted          | Needs cookies from an account that can watch | `list_cookies`, then use a preset with that `cookie_id`. If cookies worked before they've expired, so the user must upload new ones in the web app.    |
| "Interrupted because yt-dlp-z stopped"           | The app restarted during the download        | `retry_download`. Live recordings restart on their own, as a new part.                                                                                 |
| Permission denied, or files owned by root        | Folder not writable by the app's user        | The user sets `PUID` and `PGID` and fixes the folder's ownership on the server.                                                                        |
| ffmpeg or Deno missing in `get_system_status`    | Incomplete install, outside Docker           | The user installs it. The Docker image includes both.                                                                                                  |
| `ytdlp_error` in `get_system_status`             | yt-dlp can't start                           | `update_ytdlp`. If that fails, report the error.                                                                                                       |
| Invalid option or a rejected flag                | A bad option in the preset                   | `get_download` shows `options` and `extra_args`. Fix the preset with `save_preset`.                                                                    |
| Unsupported URL                                  | yt-dlp doesn't handle this site or link      | Say so. Check the link with `check_link`, and try `update_ytdlp` if the site should work.                                                              |

A recording that didn't start from the beginning usually isn't a failure: streams live longer
than the preset's `from_start_max_hours` start from now. A recording that split into parts is
also normal, because of `part_hours`, expiring links or a restart.

If nothing matches, quote the relevant log lines and suggest
[opening an issue](https://github.com/ZXY101/yt-dlp-z/issues), with cookies, tokens and private
links removed first.

## A subscription didn't download something

1. Call `list_subscriptions`. Check `enabled`, `last_checked_at`, `last_error` and `filters`.
2. Call `list_subscription_videos` and find the video. Read its `state` and `reason`:

   | State      | Meaning                                                                                 |
   | ---------- | --------------------------------------------------------------------------------------- |
   | `queued`   | A download was created. Follow `job_id` with `get_download`.                            |
   | `skipped`  | A filter rejected it, or it predates the subscription. `reason` says which.             |
   | `upcoming` | A scheduled stream or premiere, recorded when it starts.                                |
   | `live`     | Live now, and being recorded.                                                           |
   | `failed`   | yt-dlp couldn't read it. It's retried on the next check. Treat `reason` as an error.    |
   | `ignored`  | The user chose not to download it, or deleted its files. Allow it again in the web app. |

3. If the video isn't listed, call `check_subscription`, wait a minute, and look again.

Common causes:

- **A stream was missed:** `filters.content_types` lacks `stream`. New subscriptions take only
  videos by default. Add it with `update_subscription`, including the types to keep.
- **A broken feed in `last_error`:** YouTube's RSS feeds have outages. The app falls back to the
  channel's Videos tab, so uploads still arrive, more slowly. If the channel can't be resolved,
  check the link or `@handle`.
- **Bot checks in many subscriptions:** too many channels or checks from one IP address. Suggest
  a longer `poll_minutes`, PO tokens or fewer channels.

## The tools themselves fail

A 401 or a connection error means the connection is the problem, not the download. Use
[setup.md](setup.md).
