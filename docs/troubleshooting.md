# Troubleshooting and FAQ

Every job has a **Log** button on the Queue page with yt-dlp's full output.
Start there. Server logs: `docker logs yt-dlp-z`.

## Common errors

### "Sign in to confirm you're not a bot"

YouTube doesn't trust the IP address. Common with VPNs, data centres and many
channels on one address.

- Turn on [PO tokens](ytdlp.md#po-tokens).
- Use [cookies](cookies.md) from a (secondary) account.
- Check subscriptions less often and watch fewer channels.
- If it comes from a proxy, the pool already cools that proxy down and moves on
  ([Proxies](proxies.md)); VPN exits are often worse for YouTube than a home IP.

### HTTP Error 403: Forbidden, or "Requested format is not available"

Usually an outdated yt-dlp or a missing PO token.

1. Settings → yt-dlp → **Update now** (try **Nightly** if stable doesn't help).
2. Set up [PO tokens](ytdlp.md#po-tokens).

### Members-only or age-restricted videos fail

They need cookies from an account that can watch them, on the download,
preset or subscription. If it worked before, the cookies expired: export new
ones from a private window ([Cookies](cookies.md#youtube-export-from-a-private-window)).

### A subscription says the feed is broken

YouTube's RSS feeds have outages. yt-dlp-z then reads the channel's Videos tab
with yt-dlp instead, so new uploads still arrive, just more slowly. If the
channel itself can't be resolved, check the link or `@handle`.

### A playlist link downloaded the whole playlist

Links with `list=` are playlists. The Download page asks
"Just this video" or "The whole playlist"; choose the first.

### Files are owned by root / permission denied

In Docker, set `PUID` and `PGID` to your user (`id` on the host) and make sure
the mounted folders are writable by that user.

### A recording stopped after about 5 hours

YouTube's stream links expire. yt-dlp-z continues as the next part while the
stream is live ([details](live-recording.md#expiring-stream-links)). If a
recording stopped on a container stop, check `stop_grace_period` (10 minutes).

### A recording didn't start from the beginning

Streams live longer than "Record from the start, unless live longer than"
(6 hours by default) start from now. Change it on the live-stream preset
([Live recording](live-recording.md#record-from-the-start-unless-live-longer-than-n-hours)).

### "Interrupted because yt-dlp-z stopped"

The app stopped while that download ran. Press **Retry**. Live recordings
restart on their own.

### The page looks outdated after an update

Reload the page. The app tells browsers not to cache `index.html`, but an
installed home-screen shortcut can hold on to an old copy until reopened.

## FAQ

**Which sites work?** Everything [yt-dlp supports](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
for downloads. Watching channels and recording streams is YouTube-only for now.

**Can several people use it?** There's one admin account. For multiple users,
put it behind a proxy that handles login and set `YTDLPZ_AUTH_MODE=none`
([Installation](installation.md#letting-the-proxy-handle-login)).

**Does it need a YouTube API key?** No. It uses RSS feeds and yt-dlp.

**Where are my settings?** In the config folder's `yt-dlp-z.db`
([Backups](installation.md#backups)).

**Can I import my existing archive?** Not yet. A subscription's "download
recent uploads now" set to 0 starts fresh without re-downloading.

**Does it work on a Raspberry Pi?** The image uses multi-arch base images, so
it should build on arm64 (64-bit Raspberry Pi OS). Merging and long recordings
need a decent disk; use an SSD rather than an SD card.

**I forgot the password.** `docker exec -it yt-dlp-z yt-dlp-z reset-password`.

## Still stuck?

[Open an issue](https://github.com/ZXY101/yt-dlp-z/issues/new/choose) with the
yt-dlp-z and yt-dlp versions (Settings), what you did, and the job log.
**Remove cookies, tokens, passwords and private links first.**
